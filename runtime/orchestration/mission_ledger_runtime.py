import hashlib
import json
import logging
import asyncio
import sys
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

# Adds liceu-core to path so we can import the new Event Store
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../liceu-core')))
try:
    from runtime.event_store.event_store_cluster_runtime import EventStoreClusterRuntime
except ImportError:
    EventStoreClusterRuntime = None

logger = logging.getLogger(__name__)

class MissionLedgerRuntime:
    """
    Mission Ledger
    Registers: quem (who), quando (when), porque (why), resultado (result), hash
    """
    def __init__(self):
        self.ledger: List[Dict[str, Any]] = []
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

    def _generate_hash(self, record: Dict[str, Any]) -> str:
        record_string = json.dumps(record, sort_keys=True)
        return hashlib.sha256(record_string.encode('utf-8')).hexdigest()

    def record_mission_event(self, quem: str, porque: str, resultado: Dict[str, Any]) -> str:
        """
        Record a new mission event into the ledger.
        """
        quando = datetime.utcnow().isoformat()
        
        # Prepare data for hashing
        record_data = {
            "quem": quem,
            "quando": quando,
            "porque": porque,
            "resultado": resultado
        }
        
        # Generate cryptographic hash of the record
        record_hash = self._generate_hash(record_data)
        
        # Add hash to final entry
        entry = {
            **record_data,
            "hash": record_hash
        }
        
        self.ledger.append(entry)
        logger.info(f"Recorded Mission event by {quem}: hash {record_hash}")
        
        # Decide the event_type based on 'porque' or default to MISSION_EXECUTABLE
        # (This can be customized as needed based on the ledger events)
        event_type = "MISSION_EXECUTABLE"
        if "approve" in porque.lower():
            event_type = "MISSION_APPROVED"
        elif "sign" in porque.lower() or "assin" in porque.lower():
            event_type = "MISSION_SIGNED"
        elif "close" in porque.lower() or "fechar" in porque.lower():
            event_type = "MISSION_CLOSED"

        # Record in Event Store
        self._append_event(
            aggregate_id=record_hash, 
            event_type=event_type, 
            payload=entry
        )
        
        return record_hash

    def get_ledger(self) -> List[Dict[str, Any]]:
        return self.ledger
        
    def verify_integrity(self) -> bool:
        """
        Verify that all records in the ledger have not been tampered with.
        """
        for entry in self.ledger:
            stored_hash = entry["hash"]
            data_to_hash = {
                "quem": entry["quem"],
                "quando": entry["quando"],
                "porque": entry["porque"],
                "resultado": entry["resultado"]
            }
            computed_hash = self._generate_hash(data_to_hash)
            if stored_hash != computed_hash:
                logger.error(f"Integrity check failed for record: {entry}")
                return False
        return True

mission_ledger = MissionLedgerRuntime()
