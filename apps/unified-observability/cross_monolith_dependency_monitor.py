import time
import random
import json
from datetime import datetime

class CrossMonolithDependencyMonitor:
    def __init__(self):
        self.monoliths = [
            "causal-runtime",
            "collective-mind",
            "ecosystem-memory",
            "federation-authority",
            "interplanetary-gateway",
            "knowledge-graph",
            "runtime-registry"
        ]
        
    def ping_monolith(self, name: str):
        # Simulated Network Check
        latency = random.uniform(5.0, 150.0)
        status = "HEALTHY"
        if latency > 120.0:
            status = "DEGRADED"
        if random.random() < 0.05: # 5% chance of failure
            status = "DOWN"
            latency = -1
            
        return {
            "monolith": name,
            "latency_ms": round(latency, 2),
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }

    def run_health_check_sweep(self):
        results = []
        for monolith in self.monoliths:
            results.append(self.ping_monolith(monolith))
        return results

    def generate_dependency_graph(self, checks):
        """Simulates how monoliths depend on each other and identifies blocking issues."""
        down_services = [c["monolith"] for c in checks if c["status"] == "DOWN"]
        degraded = [c["monolith"] for c in checks if c["status"] == "DEGRADED"]
        
        cascading_impact = []
        if "ecosystem-memory" in down_services:
            cascading_impact.append("Knowledge Graph and Causal Runtime may fail (Data Starvation).")
        if "federation-authority" in down_services:
            cascading_impact.append("Interplanetary Gateway fully blocked (Auth Failure).")
            
        return {
            "checks": checks,
            "down_services": down_services,
            "degraded_services": degraded,
            "cascading_impact": cascading_impact
        }

if __name__ == "__main__":
    print("🌐 Inicializando Cross-Monolith Dependency Monitor...")
    monitor = CrossMonolithDependencyMonitor()
    
    print("Executando Sweep de Health Checks (Simulação)...")
    checks = monitor.run_health_check_sweep()
    graph = monitor.generate_dependency_graph(checks)
    
    print(f"✅ Monitor Report:\n{json.dumps(graph, indent=2)}")
