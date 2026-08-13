from runtime.federation.federation_event_router import FederationEventRouter


def test_digital_twin_update_is_registered_before_propagation() -> None:
    router = FederationEventRouter()

    stored_event = router.ingest(
        "DIGITAL_TWIN_UPDATED",
        {"twin_id": "continental-1", "availability": 0.994},
    )

    assert stored_event["event_id"]
    assert stored_event["contract_validated"] is True
    assert stored_event["immutable"] is True
    assert stored_event["audit"]["status"] == "PASS"
    assert router.audit_integrity(stored_event["event_id"]) is True
    assert router.route("DIGITAL_TWIN_UPDATED")[0] == "liceu"
    assert router.replay() == router.history()
    assert router.lineage(stored_event["event_id"])


def test_event_store_keeps_immutable_payload_copy() -> None:
    router = FederationEventRouter()
    payload = {"twin_id": "continental-1", "metrics": {"availability": 0.994}}

    stored_event = router.ingest("DIGITAL_TWIN_UPDATED", payload)
    payload["metrics"]["availability"] = 0.1

    assert router.history()[0]["payload"] == stored_event["payload"]