import logging
import json
from typing import Any, Dict, List
import psycopg2
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import asyncio
import sys
import os

# Adds liceu-core to path so we can import the new Event Store
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../liceu-core')))
try:
    from runtime.event_store.event_store_cluster_runtime import EventStoreClusterRuntime
except ImportError:
    EventStoreClusterRuntime = None

logger = logging.getLogger(__name__)

CAPABILITIES = {
    "build_house": "bim_arch_eng",
    "create_digital_twin": "archimedes",
    "simulate_city": "archimedes",
    "federated_reasoning": "john_brasileiro",
    "education": "academia_saber",
    "economic_projection": "econotech"
}

class CivilizationExecutionOrchestrator:
    """
    Civilization Execution Orchestrator backed by real physical datastores:
    PostgreSQL, Neo4j, and Qdrant.
    """
    
    def __init__(self, 
                 pg_dsn="dbname=liceu user=postgres password=postgres host=localhost",
                 neo4j_uri="bolt://localhost:7687", neo4j_auth=("neo4j", "password"),
                 qdrant_url="http://localhost:6333"):
        logger.info("Initializing CivilizationExecutionOrchestrator with physical datastores.")
        self.pg_dsn = pg_dsn
        self.neo4j_uri = neo4j_uri
        self.neo4j_auth = neo4j_auth
        self.qdrant_url = qdrant_url
        
        try:
            self.neo4j_driver = GraphDatabase.driver(self.neo4j_uri, auth=self.neo4j_auth)
            self.qdrant = QdrantClient(url=self.qdrant_url)
        except Exception as e:
            logger.warning(f"Could not connect to external DBs. Falling back carefully. Error: {e}")
            self.neo4j_driver = None
            self.qdrant = None

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

    def _get_pg_conn(self):
        try:
            return psycopg2.connect(self.pg_dsn)
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}")
            return None

    def _init_db(self):
        conn = self._get_pg_conn()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS plans (
                            plan_id VARCHAR(255) PRIMARY KEY,
                            status VARCHAR(50),
                            objective TEXT,
                            context JSONB
                        )
                    ''')
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS tasks (
                            task_id VARCHAR(255) PRIMARY KEY,
                            plan_id VARCHAR(255),
                            type VARCHAR(100),
                            status VARCHAR(50),
                            assigned_to VARCHAR(255)
                        )
                    ''')
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS replays (
                            id SERIAL PRIMARY KEY,
                            plan_id VARCHAR(255),
                            reason TEXT
                        )
                    ''')
                conn.commit()
            except Exception as e:
                logger.error(f"Error initializing PG DB: {e}")
            finally:
                conn.close()

    def plan(self, objective: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plans how to achieve an objective based on the context.
        """
        logger.info(f"Planning objective: {objective}")
        plan_id = f"plan_{hash(objective)}"
        
        plan_data = {"plan_id": plan_id, "status": "PLANNED", "objective": objective}
        
        # PostgreSQL
        conn = self._get_pg_conn()
        if conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO plans (plan_id, status, objective, context) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (plan_id, "PLANNED", objective, json.dumps(context))
                )
            conn.commit()
            conn.close()
            
        # Neo4j
        if self.neo4j_driver:
            with self.neo4j_driver.session() as session:
                session.run(
                    "MERGE (p:Plan {id: $plan_id, objective: $objective, status: 'PLANNED'})",
                    plan_id=plan_id, objective=objective
                )
        
        self._append_event(plan_id, "MISSION_PLANNED", plan_data)
        return plan_data

    def decompose(self, plan_id: str) -> List[Dict[str, Any]]:
        """
        Decomposes a high-level plan into executable tasks for different monoliths.
        """
        logger.info(f"Decomposing plan {plan_id}")
        
        assigned_system = "general_compute"
        conn = self._get_pg_conn()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT objective FROM plans WHERE plan_id = %s", (plan_id,))
                row = cur.fetchone()
                if row:
                    objective = row[0]
                    assigned_system = CAPABILITIES.get(objective, "general_compute")
            
        workflow_id = f"wf_{plan_id}"
        
        tasks = [
            {"task_id": f"{plan_id}_task_1", "type": "compute", "status": "PENDING", "assigned_to": assigned_system},
            {"task_id": f"{plan_id}_task_2", "type": "validate", "status": "PENDING", "assigned_to": "governance_hooks"}
        ]
        
        if conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE plans SET status = 'DECOMPOSED' WHERE plan_id = %s", (plan_id,))
                for task in tasks:
                    cur.execute(
                        "INSERT INTO tasks (task_id, plan_id, type, status, assigned_to) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                        (task["task_id"], plan_id, task["type"], task["status"], task["assigned_to"])
                    )
            conn.commit()
            conn.close()

        if self.neo4j_driver:
            with self.neo4j_driver.session() as session:
                for task in tasks:
                    session.run(
                        """
                        MATCH (p:Plan {id: $plan_id})
                        MERGE (t:Task {id: $task_id, type: $type, status: 'PENDING'})
                        MERGE (t)-[:BELONGS_TO]->(p)
                        """,
                        plan_id=plan_id, task_id=task["task_id"], type=task["type"]
                    )

        self._append_event(plan_id, "MISSION_DECOMPOSED", {"tasks": tasks})
        return tasks

    def schedule(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Schedules the decomposed tasks for execution.
        """
        logger.info(f"Scheduling {len(tasks)} tasks")
        
        conn = self._get_pg_conn()
        if conn:
            with conn.cursor() as cur:
                for task in tasks:
                    task["status"] = "SCHEDULED"
                    cur.execute("UPDATE tasks SET status = 'SCHEDULED' WHERE task_id = %s", (task["task_id"],))
            conn.commit()
            conn.close()
            
        if self.neo4j_driver:
            with self.neo4j_driver.session() as session:
                for task in tasks:
                    session.run(
                        "MATCH (t:Task {id: $task_id}) SET t.status = 'SCHEDULED'",
                        task_id=task["task_id"]
                    )
        
        if tasks:
            plan_id = tasks[0].get("plan_id", "unknown_plan")
            self._append_event(plan_id, "MISSION_SCHEDULED", {"scheduled_tasks": len(tasks)})

    def execute(self, plan_id: str) -> Dict[str, Any]:
        """
        Executes a scheduled plan.
        """
        logger.info(f"Executing plan {plan_id}")
        
        objective = "Unknown"
        conn = self._get_pg_conn()
        if conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE plans SET status = 'COMPLETED' WHERE plan_id = %s RETURNING objective", (plan_id,))
                row = cur.fetchone()
                if row:
                    objective = row[0]
            conn.commit()
            conn.close()

        if self.neo4j_driver:
            with self.neo4j_driver.session() as session:
                session.run("MATCH (p:Plan {id: $plan_id}) SET p.status = 'COMPLETED'", plan_id=plan_id)
        
        if self.qdrant:
            try:
                # Store semantic execution trace
                self.qdrant.upsert(
                    collection_name="execution_memory",
                    points=[PointStruct(
                        id=hash(plan_id) % (2**63), # Generate a valid unsigned 64-bit int
                        vector=[0.1, 0.2, 0.3], # Dummy embedding
                        payload={"plan_id": plan_id, "objective": objective, "status": "COMPLETED"}
                    )]
                )
            except Exception as e:
                logger.error(f"Failed to upsert execute record to Qdrant: {e}")
                
        execution_data = {"plan_id": plan_id, "status": "COMPLETED", "objective": objective}
        self._append_event(plan_id, "MISSION_EXECUTED", execution_data)
        
        return execution_data

    def recover(self, plan_id: str, failure_reason: str) -> None:
        """
        Recovers a plan or specific tasks in case of failure.
        """
        logger.warning(f"Recovering plan {plan_id} due to: {failure_reason}")
        
        conn = self._get_pg_conn()
        if conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE plans SET status = 'RECOVERING' WHERE plan_id = %s", (plan_id,))
                cur.execute("INSERT INTO replays (plan_id, reason) VALUES (%s, %s)", (plan_id, failure_reason))
            conn.commit()
            conn.close()

        if self.neo4j_driver:
            with self.neo4j_driver.session() as session:
                session.run(
                    """
                    MATCH (p:Plan {id: $plan_id})
                    SET p.status = 'RECOVERING'
                    MERGE (r:RecoveryAction {reason: $reason})
                    MERGE (r)-[:APPLIED_TO]->(p)
                    """,
                    plan_id=plan_id, reason=failure_reason
                )

        self._append_event(plan_id, "MISSION_RECOVERED", {"reason": failure_reason})

    def audit(self, plan_id: str) -> Dict[str, Any]:
        """
        Audits the execution traces and final status of a plan.
        """
        logger.info(f"Auditing plan {plan_id}")
        
        audit_res = {"plan_id": plan_id, "status": "UNKNOWN", "tasks": []}
        
        conn = self._get_pg_conn()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT status, objective FROM plans WHERE plan_id = %s", (plan_id,))
                row = cur.fetchone()
                if row:
                    audit_res["status"] = row[0]
                    audit_res["objective"] = row[1]
                    
                cur.execute("SELECT task_id, status FROM tasks WHERE plan_id = %s", (plan_id,))
                tasks = cur.fetchall()
                for task in tasks:
                    audit_res["tasks"].append({"task_id": task[0], "status": task[1]})
            conn.close()

        if self.neo4j_driver:
            with self.neo4j_driver.session() as session:
                session.run(
                    "MATCH (p:Plan {id: $plan_id}) MERGE (a:AuditNode {timestamp: timestamp()})-[:AUDITED]->(p)",
                    plan_id=plan_id
                )

        self._append_event(plan_id, "MISSION_AUDITED", audit_res)
        return audit_res

# Global instance backing true databases
orchestrator = CivilizationExecutionOrchestrator()
