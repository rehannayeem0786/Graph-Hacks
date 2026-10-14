"""Tests for the GraphLens agent (without LLM calls)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock
from src.agent import GraphLensAgent, SYSTEM_PROMPT
from src.graph_store import GraphStore
from src.parser import parse_codebase


@pytest.fixture
def agent():
    """Create an agent with a test graph."""
    store = GraphStore(graph_name="test_agent_graph")
    store.clear()
    result = parse_codebase(os.path.join(os.path.dirname(__file__), "..", "src"))
    store.ingest(result)
    a = GraphLensAgent(store)
    yield a
    store.clear()


def test_agent_init(agent):
    """Agent should initialize with store and empty history."""
    assert agent.store is not None
    assert agent.history == []


def test_system_prompt_has_tools():
    """System prompt should list all tools."""
    assert "impact_analysis" in SYSTEM_PROMPT
    assert "pagerank" in SYSTEM_PROMPT
    assert "find_shortest_path" in SYSTEM_PROMPT
    assert "cypher" in SYSTEM_PROMPT


def test_execute_tool_pagerank(agent):
    """Agent should execute pagerank tool."""
    result = agent._execute_tool("pagerank", {"limit": 5})
    assert "Error" not in result


def test_execute_tool_impact_analysis(agent):
    """Agent should execute impact_analysis tool."""
    result = agent._execute_tool("impact_analysis", {"name": "config", "direction": "downstream"})
    assert "Error" not in result


def test_execute_tool_unknown(agent):
    """Agent should handle unknown tools gracefully."""
    result = agent._execute_tool("nonexistent_tool", {})
    assert "Unknown tool" in result


def test_execute_tool_get_stats(agent):
    """Agent should return graph stats."""
    result = agent._execute_tool("get_stats", {})
    assert "total_nodes" in result
    assert "total_edges" in result
