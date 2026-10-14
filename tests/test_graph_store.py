"""Tests for the FalkorDB graph store."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.parser import parse_codebase
from src.graph_store import GraphStore


@pytest.fixture
def store():
    """Create a GraphStore with test data."""
    s = GraphStore(graph_name="test_graphlens")
    s.clear()
    result = parse_codebase(os.path.join(os.path.dirname(__file__), "..", "src"))
    s.ingest(result)
    yield s
    s.clear()


def test_ingest(store):
    """Ingest should create nodes and edges."""
    stats = store.get_graph_stats()
    assert stats["total_nodes"] > 0
    assert stats["total_edges"] > 0


def test_pagerank(store):
    """PageRank should return ranked nodes."""
    results = store.pagerank(5)
    assert len(results) > 0
    assert len(results[0]) >= 4  # name, type, file, score


def test_impact_analysis(store):
    """Impact analysis should find downstream dependencies."""
    results = store.impact_analysis("config")
    assert len(results) > 0


def test_community_detection(store):
    """Community detection should find file clusters."""
    results = store.community_detection()
    assert len(results) > 0


def test_get_schema(store):
    """Schema should return node labels and relationship types."""
    schema = store.get_schema()
    assert "Node labels" in schema
    assert "Relationship types" in schema


def test_query(store):
    """Raw Cypher query should work."""
    results = store.query("MATCH (n) RETURN count(n)")
    assert results[0][0] > 0
