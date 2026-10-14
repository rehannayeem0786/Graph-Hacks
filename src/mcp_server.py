"""
GraphLens MCP Server — Model Context Protocol interface.

Exposes graph tools via MCP so ANY agent framework can use them.
This is the "Tool selection through MCP" requirement from Track 01.

Usage: python -m src.mcp_server
"""

import json
import sys
from src.graph_store import GraphStore
from src.parser import parse_codebase


TOOLS = [
    {
        "name": "impact_analysis",
        "description": "Multi-hop impact analysis: what breaks if this code changes",
        "parameters": {
            "name": {"type": "string", "description": "Entity name to analyze"},
            "direction": {"type": "string", "enum": ["downstream", "upstream"]},
        },
    },
    {
        "name": "find_dependencies",
        "description": "Find module dependency chains to depth N",
        "parameters": {
            "name": {"type": "string", "description": "Module name"},
            "depth": {"type": "integer", "default": 3},
        },
    },
    {
        "name": "find_shortest_path",
        "description": "Find shortest path between two code entities",
        "parameters": {
            "source": {"type": "string"},
            "target": {"type": "string"},
        },
    },
    {
        "name": "pagerank",
        "description": "Find most critical/important code nodes",
        "parameters": {"limit": {"type": "integer", "default": 10}},
    },
    {
        "name": "trace_decision",
        "description": "Trace all connections of an entity",
        "parameters": {"name": {"type": "string"}},
    },
    {
        "name": "community_detection",
        "description": "Detect code clusters/modules",
        "parameters": {},
    },
    {
        "name": "cypher",
        "description": "Execute raw Cypher query",
        "parameters": {"query": {"type": "string"}},
    },
]


def handle_request(request: dict) -> dict:
    """Handle an MCP request."""
    method = request.get("method", "")
    params = request.get("params", {})

    if method == "tools/list":
        return {"tools": TOOLS}

    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})
        store = GraphStore()

        try:
            if tool_name == "impact_analysis":
                result = store.impact_analysis(
                    args.get("name", ""), args.get("direction", "downstream")
                )
            elif tool_name == "find_dependencies":
                result = store.find_dependencies(
                    args.get("name", ""), args.get("depth", 3)
                )
            elif tool_name == "find_shortest_path":
                result = store.find_shortest_path(
                    args.get("source", ""), args.get("target", "")
                )
            elif tool_name == "pagerank":
                result = store.pagerank(args.get("limit", 10))
            elif tool_name == "trace_decision":
                result = store.trace_decision(args.get("name", ""))
            elif tool_name == "community_detection":
                result = store.community_detection()
            elif tool_name == "cypher":
                result = store.query(args.get("query", ""))
            else:
                return {"error": f"Unknown tool: {tool_name}"}

            return {"result": json.dumps(result, default=str)}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Unknown method: {method}"}


def main():
    """Run MCP server over stdin/stdout."""
    print("GraphLens MCP Server ready", file=sys.stderr)
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON"}), flush=True)


if __name__ == "__main__":
    main()