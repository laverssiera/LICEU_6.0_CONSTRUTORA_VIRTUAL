import aiohttp
import asyncio
import time
import json
import logging
import uuid
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

async def test_1_civilization_bootstrap(session):
    logger.info("=== TESTE 1: CIVILIZATION BOOTSTRAP ===")
    start_time = time.time()
    try:
        async with session.get(f"{BASE_URL}/civilization/state", timeout=1.0) as resp:
            data = await resp.json()
            latency = (time.time() - start_time) * 1000
            
            assert resp.status == 200, f"Expected 200, got {resp.status}"
            assert "metrics" in data, "No metrics in response"
            metrics = data["metrics"]
            assert "federation_health" in metrics, "No federation_health"
            assert "missions_active" in metrics, "No missions_active"
            assert "contracts_active" in metrics, "No contracts_active"
            assert "twins_active" in metrics, "No twins_active"
            assert latency < 500, f"Latency too high: {latency}ms"
            
            logger.info(f"SUCCESS: Bootstrap valid! Latency: {latency:.2f}ms. State: {json.dumps(data)}")
            return True
    except Exception as e:
        logger.error(f"FAILED: {e}")
        return False

async def test_3_contract_enforcement(session):
    logger.info("=== TESTE 3: CONTRACT ENFORCEMENT ===")
    payload = {
        "event": "DIGITALTWINUPDATED",  # Wrong! Should be DIGITAL_TWIN_UPDATED
        "version": "1.0.0"
    }
    try:
        # Tenta injetar no endpoint de registro/validate novo 
        async with session.post(f"{BASE_URL}/contracts/validate", json=payload) as resp:
            data = await resp.json()
            
            assert data["valid"] == False, "O validator aceitou o payload espúrio sem event_type formal!"
            logger.info(f"SUCCESS: Contract Validator correctly rejected invalid event format. {data}")
            return True
    except Exception as e:
        logger.error(f"FAILED: {e}")
        return False

async def test_4_federation_cascade(session):
    logger.info("=== TESTE 4: FEDERATION CASCADE ===")
    try:
        # Chama a injeção do impact de ARCHIMEDES
        async with session.get(f"{BASE_URL}/federation/dependency/ARCHIMEDES/impact") as resp:
            data = await resp.json()
            assert data["status"] == "CRITICAL_IMPACT"
            assert "blast_radius" in data
            
            radius = data["blast_radius"]
            assert len(radius.get("impacts_missions", [])) > 0, "Dependency Graph missing impacted missions"
            logger.info(f"SUCCESS: Dependency graph successfully tracked blast radius for ARCHIMEDES failure. Impacts: {radius['impacts_missions']}")
            return True
    except Exception as e:
        logger.error(f"FAILED: {e}")
        return False

async def main():
    async with aiohttp.ClientSession() as session:
        t1 = await test_1_civilization_bootstrap(session)
        t3 = await test_3_contract_enforcement(session)
        t4 = await test_4_federation_cascade(session)
        
        # Testes de stress ou que invocam apps devem ser disparados pelo pytest/integrações rodando o monolito vivo

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(main())
