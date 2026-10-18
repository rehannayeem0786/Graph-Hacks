"""Tests for the FalkorDB graph store."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.parser import parse_codebase
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
def store():
    """Create a GraphStore with test data."""
    s = GraphStore(graph_name="test_graphlens")
    s.clear()
    result = parse_codebase(os.path.join(os.path.dirname(__file__), "..", "src"))
    s.ingest(result)
    yield s
    s.clear()


@requires_falkordb
def test_ingest(store):
    """Ingest should create nodes and edges."""
    stats = store.get_graph_stats()
    assert stats["total_nodes"] > 0
    assert stats["total_edges"] > 0


@requires_falkordb
def test_pagerank(store):
    """PageRank should return ranked nodes."""
    results = store.pagerank(5)
    assert len(results) > 0
    assert len(results[0]) >= 4  # name, type, file, score


@requires_falkordb
def test_impact_analysis(store):
    """Impact analysis should find downstream dependencies."""
    results = store.impact_analysis("config.py")
    assert len(results) > 0


@requires_falkordb
def test_community_detection(store):
    """Community detection should find file clusters."""
    results = store.community_detection()
    assert len(results) > 0


@requires_falkordb
def test_get_schema(store):
    """Schema should return node labels and relationship types."""
    schema = store.get_schema()
    assert "Node labels" in schema
    assert "Relationship types" in schema


@requires_falkordb
def test_query(store):
    """Raw Cypher query should work."""
    results = store.query("MATCH (n) RETURN count(n)")
    assert results[0][0] > 0


@requires_falkordb
def test_link_definitions_and_shortest_path(store):
    """Call→definition links let the BFS fallback find cross-component paths."""
    link_stats = store.link_definitions()
    assert link_stats["resolved_calls"] > 0, "expected Call→definition links"

    path = store.find_shortest_path("parse_codebase", "GraphStore")
    assert path, "expected a path between parse_codebase and GraphStore"
    nodes, edges = path[0][0], path[0][1]
    assert "parse_codebase" in nodes[0]
    assert "GraphStore" in nodes[-1]
    assert len(edges) == len(nodes) - 1
    if len(path[0]) > 3:
        assert len(path[0][3]) == len(edges)
