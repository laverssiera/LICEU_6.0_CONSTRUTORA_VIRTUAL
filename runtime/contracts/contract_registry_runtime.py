from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import asyncio
import sys
import os
from fastapi import APIRouter, HTTPException

# Adds liceu-core to path so we can import the new Event Store
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../liceu-core')))
try:
    from runtime.event_store.event_store_cluster_runtime import EventStoreClusterRuntime
except ImportError:
    EventStoreClusterRuntime = None

router = APIRouter()

class UniversalContractRegistry:
    def __init__(self):
        self.contracts = {}
        if EventStoreClusterRuntime:
            self.event_store = EventStoreClusterRuntime()
        else:
            self.event_store = None
            
    def _append_event(self, aggregate_id: str, event_type: str, payload: dict):
        if self.event_store:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.event_store.append(aggregate_id, event_type, payload))
                else:
                    loop.run_until_complete(self.event_store.append(aggregate_id, event_type, payload))
            except RuntimeError:
                asyncio.run(self.event_store.append(aggregate_id, event_type, payload))
        
    def register_contract(self, contract_type: str, data: Dict[str, Any]) -> str:
        contract_types = [
            "MissionContract", 
            "SpatialContract", 
            "EconomicContract", 
            "LegalContract", 
            "SupplierContract", 
            "ScientificContract"
        ]
        
        if contract_type not in contract_types:
            raise ValueError(f"Invalid contract type. Must be one of {contract_types}")
            
        contract_id = f"contract_{len(self.contracts) + 1}_{contract_type}"
        self.contracts[contract_id] = {
            "contract_id": contract_id,
            "type": contract_type,
            "data": data,
            "status": "REGISTERED",
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat(),
            "history": [{"event": "REGISTERED", "timestamp": datetime.utcnow().isoformat()}]
        }
        
        self._append_event(
            aggregate_id=contract_id,
            event_type="CONTRACT_REGISTERED",
            payload={
                "contract_id": contract_id,
                "contract_type": contract_type,
                "version": "1.0.0",
                "data": data
            }
        )
        return contract_id

    def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        return self.contracts.get(contract_id)

    def get_history(self, contract_id: str) -> List[Dict[str, Any]]:
        contract = self.contracts.get(contract_id)
        if not contract:
            return []
        return contract.get("history", [])

    def update_contract(self, contract_id: str, data: Dict[str, Any]) -> str:
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError("Contract not found")
        
        # Increment simple version for demo purposes
        parts = contract.get("version", "1.0.0").split(".")
        new_version = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
        
        contract["data"] = data
        contract["version"] = new_version
        contract["status"] = "UPDATED"
        contract["history"].append({"event": "UPDATED", "timestamp": datetime.utcnow().isoformat(), "version": new_version})
        
        payload = {
            "contract_id": contract_id,
            "version": new_version,
            "data": data
        }
        self._append_event(contract_id, "CONTRACT_UPDATED", payload)
        self._append_event(contract_id, "CONTRACT_VERSION_CREATED", {"version": new_version})
        return new_version

    def approve_contract(self, contract_id: str) -> bool:
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError("Contract not found")
            
        contract["status"] = "APPROVED"
        contract["history"].append({"event": "APPROVED", "timestamp": datetime.utcnow().isoformat()})
        
        self._append_event(contract_id, "CONTRACT_APPROVED", {"status": "APPROVED"})
        return True

    def deprecate_contract(self, contract_id: str, reason: str = "Outdated") -> bool:
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError("Contract not found")
            
        contract["status"] = "DEPRECATED"
        contract["history"].append({"event": "DEPRECATED", "reason": reason, "timestamp": datetime.utcnow().isoformat()})
        
        self._append_event(contract_id, "CONTRACT_DEPRECATED", {"reason": reason, "status": "DEPRECATED"})
        return True

    def validate_contract(self, contract_id: str, is_valid: bool, issues: List[str] = None) -> bool:
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError("Contract not found")
        
        if is_valid:
            contract["status"] = "VALIDATED"
            contract["history"].append({"event": "VALIDATED", "timestamp": datetime.utcnow().isoformat()})
            self._append_event(contract_id, "CONTRACT_VALIDATED", {"status": "VALIDATED"})
        else:
            contract["status"] = "REJECTED"
            contract["history"].append({"event": "REJECTED", "issues": issues, "timestamp": datetime.utcnow().isoformat()})
            self._append_event(contract_id, "CONTRACT_REJECTED", {"issues": issues})
        
        return is_valid
        
    def publish_to_federation(self, contract_id: str, domain: str) -> bool:
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError("Contract not found")
            
        contract["history"].append({"event": "FEDERATION_PUBLISHED", "domain": domain, "timestamp": datetime.utcnow().isoformat()})
        self._append_event(contract_id, "CONTRACT_FEDERATION_PUBLISHED", {"domain": domain})
        return True

registry = UniversalContractRegistry()

@router.post("/contracts/register")
def register_contract(payload: Dict[str, Any]):
    try:
        contract_type = payload.get("contract_type")
        if not contract_type:
            raise HTTPException(status_code=400, detail="contract_type is required")
            
        contract_id = registry.register_contract(contract_type, payload.get("data", {}))
        return {"status": "success", "contract_id": contract_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/contracts/{contract_id}")
def get_contract(contract_id: str):
    contract = registry.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract

@router.get("/contracts/history")
def get_contracts_history(contract_id: str):
    history = registry.get_history(contract_id)
    if not history:
        raise HTTPException(status_code=404, detail="Contract history not found or empty")
    return {"contract_id": contract_id, "history": history}

@router.put("/contracts/{contract_id}")
def update_contract(contract_id: str, payload: Dict[str, Any]):
    try:
        new_version = registry.update_contract(contract_id, payload.get("data", {}))
        return {"status": "success", "contract_id": contract_id, "version": new_version}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/contracts/{contract_id}/approve")
def approve_contract(contract_id: str):
    try:
        registry.approve_contract(contract_id)
        return {"status": "success", "contract_id": contract_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/contracts/{contract_id}/deprecate")
def deprecate_contract(contract_id: str, payload: Dict[str, Any]):
    try:
        reason = payload.get("reason", "Outdated")
        registry.deprecate_contract(contract_id, reason=reason)
        return {"status": "success", "contract_id": contract_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/contracts/{contract_id}/validate")
def validate_contract(contract_id: str, payload: Dict[str, Any]):
    try:
        is_valid = payload.get("is_valid", True)
        issues = payload.get("issues", [])
        registry.validate_contract(contract_id, is_valid=is_valid, issues=issues)
        return {"status": "success", "contract_id": contract_id, "is_valid": is_valid}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/contracts/{contract_id}/publish")
def publish_to_federation(contract_id: str, payload: Dict[str, Any]):
    try:
        domain = payload.get("domain", "interplanetary")
        registry.publish_to_federation(contract_id, domain=domain)
        return {"status": "success", "contract_id": contract_id, "domain": domain}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

