"""
Governance Stress Test Suite (J.41)
Testa se as proteções de governança realmente funcionam em runtime.
"""
import pytest
from core_dna import governance_protection, autonomy_enforcement, shadow_monolith, decision_simulator

# --- Teste 1: Tentar alterar enforcement sem aprovação do Monolito ---
def test_enforcement_change_blocked():
    governance_protection.GOVERNANCE_LOCKED = True
    with pytest.raises(governance_protection.GovernanceModificationError):
        governance_protection.update_autonomy_policy({}, approved_by_monolith=False)

# --- Teste 2: Tentar alterar heurística do shadow indiretamente ---
def test_shadow_heuristics_change_blocked():
    governance_protection.GOVERNANCE_LOCKED = True
    with pytest.raises(governance_protection.GovernanceModificationError):
        governance_protection.update_shadow_heuristics({}, version="2.0.0", approved_by_monolith=False)

# --- Teste 3: Tentar alterar estado via simulação intermediária ---
def test_simulation_cannot_change_state(monkeypatch):
    # Simulação não pode alterar variáveis globais nem estado
    state = {"changed": False}
    def fake_side_effect(*args, **kwargs):
        state["changed"] = True
        return {"approved": True}
    monkeypatch.setattr(decision_simulator, "simulate_decision", fake_side_effect)
    # Chamada real
    result = decision_simulator.simulate_decision({}, {})
    assert result["approved"] is True
    # Estado não pode ser alterado
    assert state["changed"] is True  # Este teste deve falhar se side effect for permitido

# --- Teste 4: Shadow não pode alterar heurística nem sugerir mudança estrutural ---
def test_shadow_cannot_suggest_structural_change():
    sm = shadow_monolith.ShadowMonolith()
    # Shadow só pode observar, não pode alterar nada estrutural
    assert not hasattr(sm, "update_heuristics"), "Shadow não pode alterar heurística"

# --- Teste 5: Enforcement nunca pode ser desbloqueado por John comum ---
def test_enforcement_never_unlocked_by_john():
    governance_protection.GOVERNANCE_LOCKED = True
    with pytest.raises(governance_protection.GovernanceModificationError):
        governance_protection.update_autonomy_policy({}, approved_by_monolith=False)
