"""Tests for the FastAPI server — covers all endpoints including new Track 02 features."""

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


def test_suggestions(client):
    """Suggestions endpoint should return demo questions."""
    response = client.get("/suggestions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    assert "q" in data[0]


def test_dashboard(client):
    """Dashboard should return HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "GraphLens" in response.text


@requires_falkordb
def test_graph_search(client):
    """Search endpoint should return results."""
    response = client.get("/graph/search?q=parser&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@requires_falkordb
def test_graph_json(client):
    """Graph JSON endpoint should return nodes and edges."""
    response = client.get("/graph?limit=50")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data


@requires_falkordb
def test_pagerank(client):
    """PageRank endpoint should return ranked nodes."""
    response = client.get("/graph/pagerank?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@requires_falkordb
def test_communities(client):
    """Community detection endpoint."""
    response = client.get("/graph/communities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@requires_falkordb
def test_cypher_playground(client):
    """Cypher playground should execute read-only queries."""
    response = client.post("/graph/cypher", json={"query": "MATCH (n) RETURN n.name LIMIT 3"})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


@requires_falkordb
def test_cypher_blocks_destructive(client):
    """Cypher playground should block DELETE queries."""
    response = client.post("/graph/cypher", json={"query": "MATCH (n) DELETE n"})
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "Read-only" in data["error"]


@requires_falkordb
def test_memory_list(client):
    """Memory endpoint should return list."""
    response = client.get("/memory")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@requires_falkordb
def test_memory_store(client):
    """Memory store endpoint should save a fact."""
    response = client.post("/memory", json={"fact": "test fact from pytest", "category": "test"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stored"


@requires_falkordb
def test_multi_agent_state(client):
    """Multi-agent state endpoint should return state."""
    response = client.get("/multi-agent/state")
    assert response.status_code == 200
    data = response.json()
    assert "active_agents" in data or "agents" in data


@requires_falkordb
def test_multi_agent_analyze(client):
    """Multi-agent analysis should coordinate agents."""
    response = client.post("/multi-agent/analyze")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) >= 3
    assert data["tasks_completed"] == 3


@requires_falkordb
def test_ask_endpoint(client):
    """Ask endpoint should return answer with trace."""
    response = client.post("/ask", json={"question": "What is the graph schema?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "trace" in data
    assert "path_nodes" in data


@requires_falkordb
def test_graph_schema(client):
    """Schema endpoint should return node types, edge types, and patterns."""
    response = client.get("/graph/schema")
    assert response.status_code == 200
    data = response.json()
    assert "node_types" in data
    assert "edge_types" in data
    assert "patterns" in data
    assert "total_nodes" in data


def test_favicon(client):
    """Favicon should return 204."""
    response = client.get("/favicon.ico")
    assert response.status_code == 204


@requires_falkordb
def test_stats_has_timing(client):
    """Stats should include query timing."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "query_time_ms" in data
    assert isinstance(data["query_time_ms"], float)
