import json
import logging
import asyncio
import sys
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter, HTTPException

# Adds liceu-core to path so we can import the Event Store
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../liceu-core')))
try:
    from runtime.event_store.event_store_cluster_runtime import EventStoreClusterRuntime
except ImportError:
    EventStoreClusterRuntime = None

logger = logging.getLogger(__name__)

router = APIRouter()

class FederationSchemaRegistry:
    """
    Federation Schema Registry
    Persists OpenAPI, Pydantic, and EventSchemas to PostgreSQL.
    Tightly coupled to the Event Store for temporal truth and governance.
    """
    def __init__(self, db_dsn: str = "dbname=liceu user=postgres password=postgres host=localhost"):
        self.db_dsn = db_dsn
        self.fallback_memory = {}
        if EventStoreClusterRuntime:
            self.event_store = EventStoreClusterRuntime()
        else:
            self.event_store = None
        self._init_db()

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

    def _get_connection(self):
        try:
            return psycopg2.connect(self.db_dsn)
        except Exception as e:
            return None

    def _init_db(self):
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS federation_schemas (
                        schema_id VARCHAR(255) PRIMARY KEY,
                        schema_type VARCHAR(50) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        version VARCHAR(50) NOT NULL,
                        definition JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # Add columns for governance evolution if missing
                for col, defn in [
                    ("status", "VARCHAR(50) DEFAULT 'REGISTERED'"), 
                    ("domain", "VARCHAR(100)"), 
                    ("history", "JSONB DEFAULT '[]'::jsonb")
                ]:
                    try:
                        cursor.execute(f"ALTER TABLE federation_schemas ADD COLUMN IF NOT EXISTS {col} {defn}")
                    except Exception:
                        pass
            conn.commit()
        except Exception as e:
            logger.error(f"Error initializing schema registry DB: {e}")
        finally:
            conn.close()

    def _fetch_from_db_or_memory(self, schema_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute('SELECT * FROM federation_schemas WHERE schema_id = %s', (schema_id,))
                    row = cursor.fetchone()
                    if row:
                        ans = dict(row)
                        if isinstance(ans.get("history"), str):
                            ans["history"] = json.loads(ans["history"])
                        return ans
            except Exception as e:
                logger.error(f"Fetch failed: {e}")
            finally:
                conn.close()
        return self.fallback_memory.get(schema_id)

    def _save_to_db_or_memory(self, schema_id: str, record: Dict[str, Any]):
        self.fallback_memory[schema_id] = record
        conn = self._get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO federation_schemas (schema_id, schema_type, name, version, definition, status, domain, history, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (schema_id) DO UPDATE SET 
                            definition = EXCLUDED.definition, 
                            status = EXCLUDED.status,
                            domain = EXCLUDED.domain,
                            history = EXCLUDED.history,
                            version = EXCLUDED.version
                    ''', (
                        schema_id, record["schema_type"], record["name"], record["version"],
                        json.dumps(record["definition"]), record["status"], record.get("domain"),
                        json.dumps(record["history"]), datetime.utcnow()
                    ))
                conn.commit()
            except Exception as e:
                logger.error(f"Save failed: {e}")
            finally:
                conn.close()

    def register_schema(self, schema_type: str, name: str, version: str, definition: Dict[str, Any]) -> str:
        valid_types = ["OpenAPI", "Pydantic", "EventSchemas"]
        if schema_type not in valid_types:
            raise ValueError(f"Invalid schema type must be one of {valid_types}")
            
        schema_id = f"{schema_type}_{name}_{version}".lower().replace(" ", "_")
        
        history_entry = {"event": "REGISTERED", "timestamp": datetime.utcnow().isoformat()}
        record = {
            "schema_id": schema_id,
            "schema_type": schema_type,
            "name": name,
            "version": version,
            "definition": definition,
            "status": "REGISTERED",
            "domain": None,
            "history": [history_entry]
        }
        self._save_to_db_or_memory(schema_id, record)
        
        self._append_event(schema_id, "SCHEMA_REGISTERED", {
            "schema_id": schema_id, "name": name, "version": version, "schema_type": schema_type
        })
        return schema_id

    def update_schema(self, schema_id: str, new_definition: Dict[str, Any], new_version: str) -> str:
        record = self._fetch_from_db_or_memory(schema_id)
        if not record:
            raise ValueError("Schema not found")
        
        record["definition"] = new_definition
        record["version"] = new_version
        record["status"] = "UPDATED"
        record["history"] = record.get("history", [])
        record["history"].append({"event": "UPDATED", "version": new_version, "timestamp": datetime.utcnow().isoformat()})
        self._save_to_db_or_memory(schema_id, record)

        self._append_event(schema_id, "SCHEMA_UPDATED", {"version": new_version})
        return new_version

    def approve_schema(self, schema_id: str) -> bool:
        record = self._fetch_from_db_or_memory(schema_id)
        if not record:
            raise ValueError("Schema not found")

        record["status"] = "APPROVED"
        record["history"] = record.get("history", [])
        record["history"].append({"event": "APPROVED", "timestamp": datetime.utcnow().isoformat()})
        self._save_to_db_or_memory(schema_id, record)

        self._append_event(schema_id, "SCHEMA_APPROVED", {"status": "APPROVED"})
        return True

    def deprecate_schema(self, schema_id: str) -> bool:
        record = self._fetch_from_db_or_memory(schema_id)
        if not record:
            raise ValueError("Schema not found")

        record["status"] = "DEPRECATED"
        record["history"] = record.get("history", [])
        record["history"].append({"event": "DEPRECATED", "timestamp": datetime.utcnow().isoformat()})
        self._save_to_db_or_memory(schema_id, record)

        self._append_event(schema_id, "SCHEMA_DEPRECATED", {"status": "DEPRECATED"})
        return True

    def publish_schema(self, schema_id: str, domain: str) -> bool:
        record = self._fetch_from_db_or_memory(schema_id)
        if not record:
            raise ValueError("Schema not found")

        record["domain"] = domain
        record["status"] = "PUBLISHED"
        record["history"] = record.get("history", [])
        record["history"].append({"event": "PUBLISHED", "domain": domain, "timestamp": datetime.utcnow().isoformat()})
        self._save_to_db_or_memory(schema_id, record)

        self._append_event(schema_id, "SCHEMA_PUBLISHED", {"domain": domain})
        return True

    def validate_payload(self, schema_id: str, payload_data: Dict[str, Any], is_valid: bool = True, issues: List[str] = None) -> bool:
        record = self._fetch_from_db_or_memory(schema_id)
        if not record:
            raise ValueError("Schema not found")
            
        event_name = "SCHEMA_VALIDATED" if is_valid else "SCHEMA_VALIDATION_FAILED"
        
        # Log validation check directly to history
        record["history"] = record.get("history", [])
        record["history"].append({
            "event": event_name, 
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat()
        })
        self._save_to_db_or_memory(schema_id, record)
        
        self._append_event(schema_id, event_name, {"is_valid": is_valid, "issues": issues})
        return is_valid

    def get_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
        return self._fetch_from_db_or_memory(schema_id)

    def get_schemas(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute('SELECT schema_id, name, version, status, domain FROM federation_schemas')
                    return [dict(r) for r in cursor.fetchall()]
            except:
                pass
            finally:
                conn.close()
        return [{"schema_id": s["schema_id"], "status": s["status"]} for s in self.fallback_memory.values()]

registry = FederationSchemaRegistry()

# ----------------------------------------------------
# API ENDPOINTS
# ----------------------------------------------------

@router.post("/schemas/register")
def api_register_schema(payload: Dict[str, Any]):
    try:
        schema_type = payload.get("schema_type", "EventSchemas")
        name = payload.get("name")
        version = payload.get("version", "1.0.0")
        definition = payload.get("definition", {})
        if not name:
            raise HTTPException(status_code=400, detail="name is required")
            
        schema_id = registry.register_schema(schema_type, name, version, definition)
        return {"status": "success", "schema_id": schema_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/schemas/{schema_id}/approve")
def api_approve_schema(schema_id: str):
    try:
        registry.approve_schema(schema_id)
        return {"status": "success", "schema_id": schema_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/schemas/{schema_id}/publish")
def api_publish_schema(schema_id: str, payload: Dict[str, Any]):
    try:
        domain = payload.get("domain", "interplanetary")
        registry.publish_schema(schema_id, domain)
        return {"status": "success", "schema_id": schema_id, "domain": domain}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/schemas/{schema_id}/validate")
def api_validate_schema(schema_id: str, payload: Dict[str, Any]):
    try:
        is_valid = payload.get("is_valid", True)
        issues = payload.get("issues", [])
        payload_data = payload.get("payload_data", {})
        result = registry.validate_payload(schema_id, payload_data, is_valid, issues)
        return {"status": "success", "schema_id": schema_id, "is_valid": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/schemas/{schema_id}/deprecate")
def api_deprecate_schema(schema_id: str):
    try:
        registry.deprecate_schema(schema_id)
        return {"status": "success", "schema_id": schema_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/schemas")
def api_get_schemas():
    return {"schemas": registry.get_schemas()}

@router.get("/schemas/history")
def api_get_schemas_history(schema_id: str):
    schema = registry.get_schema(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return {"schema_id": schema_id, "history": schema.get("history", [])}

@router.get("/schemas/{schema_id}/lineage")
def api_get_schema_lineage(schema_id: str):
    schema = registry.get_schema(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # In a real lineage trace, we would query the EventStore backwards
    # based on the causation_id or schema semantic parent.
    history = schema.get("history", [])
    return {
        "schema_id": schema_id,
        "name": schema.get("name"),
        "version": schema.get("version"),
        "events": history
    }
