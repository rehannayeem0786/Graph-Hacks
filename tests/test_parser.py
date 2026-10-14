"""Tests for the AST parser."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.parser import parse_codebase, parse_python_file, ParseResult


def test_parse_codebase_finds_nodes():
    """Parser should find nodes in the src directory."""
    result = parse_codebase(os.path.join(os.path.dirname(__file__), "..", "src"))
    assert len(result.nodes) > 0
    assert len(result.edges) > 0


def test_parse_python_file():
    """Parser should extract functions, classes, imports from a file."""
    test_file = os.path.join(os.path.dirname(__file__), "..", "src", "config.py")
    result = parse_python_file(test_file, "src/config.py")
    assert len(result.nodes) > 0
    node_types = {n.node_type for n in result.nodes}
    assert "Module" in node_types


def test_parse_result_structure():
    """ParseResult should correctly store nodes and edges."""
    result = ParseResult()
    assert len(result.nodes) == 0
    assert len(result.edges) == 0


def test_node_types():
    """Parser should identify correct node types."""
    result = parse_codebase(os.path.join(os.path.dirname(__file__), "..", "src"))
    node_types = {n.node_type for n in result.nodes}
    assert "Module" in node_types
    assert "Function" in node_types
    assert "Class" in node_types


def test_edge_types():
    """Parser should identify correct edge types."""
    result = parse_codebase(os.path.join(os.path.dirname(__file__), "..", "src"))
    edge_types = {e.edge_type for e in result.edges}
    assert "CONTAINS" in edge_types
    assert "IMPORTS" in edge_types
    assert "CALLS" in edge_types
