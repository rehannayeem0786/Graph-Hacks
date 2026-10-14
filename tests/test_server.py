"""Tests for the FastAPI server."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from src.server import app


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


def test_stats(client):
    """Stats endpoint should return graph statistics."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_nodes" in data
    assert "total_edges" in data
