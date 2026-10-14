"""Tests for the FastAPI server."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from src.server import app
from src.graph_store import GraphStore


def _falkordb_available():
    """Check if FalkorDB is running."""
    try:
        s = GraphStore(graph_name="test_connectivity_check")
        s.query("RETURN 1")
        return True
    except Exception:
        return False


requires_falkordb = pytest.mark.skipif(
    not _falkordb_available(),
    reason="FalkorDB not running (start with: docker run -p 6379:6379 falkordb/falkordb:latest)"
)


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    """Health endpoint should return ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "GraphLens"


@requires_falkordb
def test_stats(client):
    """Stats endpoint should return graph statistics."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_nodes" in data
    assert "total_edges" in data
