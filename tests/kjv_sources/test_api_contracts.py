from fastapi.testclient import TestClient

from src.kjv_sources import api


class _DummyClient:
    collection_name = "kjv_sources"

    def get_collection_stats(self):
        return {"collection_name": "kjv_sources", "total_points": 42, "status": "green"}

    def get_doublet_statistics(self):
        return {
            "total_verses": 10,
            "doublet_verses": 3,
            "non_doublet_verses": 7,
            "unique_doublet_count": 2,
            "source_codes": ["J", "E", "P", "R"],
            "source_doublet_distribution": {"J": 2, "E": 1, "P": 1, "R": 0},
            "source_transitions": [{"source": "J", "target": "P", "value": 1}],
            "inter_source_doublets": [{"source": "J", "target": "P", "value": 1}],
            "source_transition_by_category": [],
            "inter_source_doublets_by_category": [],
            "doublet_categories": {"cosmogony": 1},
            "doublets_by_book": {"Genesis": 2, "Exodus": 1},
        }


def test_health_endpoint():
    client = TestClient(api.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_endpoint_with_stubbed_client(monkeypatch):
    monkeypatch.setattr(api, "get_qdrant_client", lambda: _DummyClient())
    client = TestClient(api.app)
    response = client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["total_points"] == 42


def test_source_flow_network_contract(monkeypatch):
    monkeypatch.setattr(api, "get_qdrant_client", lambda: _DummyClient())
    client = TestClient(api.app)
    response = client.get("/api/v1/bird-eye/source-flow-network")
    assert response.status_code == 200
    payload = response.json()
    assert "nodes" in payload
    assert "sankey" in payload
    assert "chord" in payload
    assert "meta" in payload
