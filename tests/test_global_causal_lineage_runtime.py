from runtime.global_causal_lineage_runtime import GlobalCausalLineageRuntime


def test_global_causal_lineage_validates_event_decision_execution_impact_and_twin() -> None:
    runtime = GlobalCausalLineageRuntime()

    result = runtime.validate_global_lineage(
        continente_origem="A",
        event_id="evt-001",
        trace_id="trace-001",
        decision_id="dec-001",
        execution_id="exec-001",
        impact_id="impact-001",
        continente_destino="C",
        continent_path=["A", "B", "C"],
        twin_id="twin-001",
    )

    assert result["global_lineage_valid"] is True
    assert result["chain"] == ["evt-001", "dec-001", "exec-001", "impact-001", "twin-001"]
    assert result["caused_by"] == "evt-001"
    assert result["derived_from"] == "dec-001"
    assert result["propagated_to"] == ["A", "B", "C"]
    assert result["impacted"] == "impact-001"
    assert result["reconciled_by"] == "twin-001"
    assert result["status"] == "PASS"


def test_global_causal_lineage_rejects_missing_chain_hops() -> None:
    runtime = GlobalCausalLineageRuntime()

    result = runtime.validate_global_lineage(
        continente_origem="A",
        event_id="evt-002",
        trace_id="trace-002",
        decision_id="",
        execution_id="exec-002",
        impact_id="impact-002",
        continente_destino="C",
        continent_path=["A", "B", "C"],
        twin_id="twin-002",
    )

    assert result["global_lineage_valid"] is False
    assert result["status"] == "FAIL"
    assert "missing_decision_id" in result["reasons"]
