"""
GraphLens Visualization — generate interactive graph visualizations.

Produces D3.js-compatible JSON for the web UI and ASCII art for CLI.
This makes the graph EXPLAINABLE — judges can see the actual paths.
"""

import json
from src.graph_store import GraphStore


def get_graph_json(store: GraphStore, limit: int = 500) -> dict:
    """Get the full architectural graph as D3.js force-directed graph JSON."""
    nodes_raw = store.query(f"""
        MATCH (n)
        WHERE NOT n:Call
        RETURN n.id AS id, n.name AS name, labels(n)[0] AS type,
               n.file AS file, n.line_start AS line_start
        ORDER BY CASE labels(n)[0]
            WHEN 'Module' THEN 1
            WHEN 'Class' THEN 2
            WHEN 'Function' THEN 3
            WHEN 'Method' THEN 4
            WHEN 'ExternalModule' THEN 5
            ELSE 6 END
        LIMIT {limit}
    """)
    edges_raw = store.query(f"""
        MATCH (a)-[r]->(b)
        WHERE NOT a:Call AND NOT b:Call
        RETURN a.id AS source, b.id AS target, type(r) AS type, r.line AS line
        LIMIT {limit * 2}
    """)

    nodes = []
    node_ids = set()
    for row in nodes_raw:
        node_id = row[0]
        if node_id in node_ids:
            continue
        node_ids.add(node_id)
        nodes.append({
            "id": node_id,
            "label": row[1] or node_id,
            "type": row[2] or "Node",
            "file": row[3] or "",
            "line": row[4] or 0,
        })

    edges = []
    for row in edges_raw:
        if row[0] in node_ids and row[1] in node_ids:
            edges.append({
                "source": row[0],
                "target": row[1],
                "type": row[2] or "RELATES",
                "line": row[3] or 0,
            })

    return {"nodes": nodes, "edges": edges}


def get_path_visualization(store: GraphStore, source: str, target: str) -> dict:
    """Visualize the shortest path between two entities."""
    try:
        results = store.find_shortest_path(source, target)
    except Exception as e:
        return {"path": [], "message": f"Query error: {str(e)}", "hops": 0, "nodes": [], "edges": []}

    if not results or not results[0] or not results[0][0]:
        return {"path": [], "message": f"No path found between '{source}' and '{target}'", "hops": 0, "nodes": [], "edges": []}

    path_nodes = results[0][0]
    path_edges = results[0][1]

    visualization = []
    for i, node_name in enumerate(path_nodes):
        visualization.append({"node": node_name, "step": i})
        if i < len(path_edges):
            visualization.append({"edge": path_edges[i], "step": i})

    # ASCII representation
    ascii_path = f" {path_nodes[0]} "
    for i, edge_type in enumerate(path_edges):
        ascii_path += f"-[{edge_type}]-> {path_nodes[i + 1]} "

    return {
        "path": visualization,
        "ascii": ascii_path,
        "hops": len(path_edges),
        "nodes": path_nodes,
        "edges": path_edges,
    }


def get_impact_visualization(store: GraphStore, node_name: str, direction: str = "downstream") -> dict:
    """Visualize impact analysis as a tree."""
    results = store.impact_analysis(node_name, direction)

    tree = {"root": node_name, "affected": [], "total_hops": 0}
    for row in results:
        affected_name = row[0]
        file_path = row[1] if len(row) > 1 else ""
        distance = row[2] if len(row) > 2 else 0
        path_types = row[3] if len(row) > 3 else []
        tree["affected"].append({
            "name": affected_name,
            "file": file_path,
            "distance": distance,
            "via": path_types,
        })
        tree["total_hops"] = max(tree["total_hops"], distance)

    return tree


def get_community_visualization(store: GraphStore) -> list:
    """Get communities as clusters for visualization."""
    results = store.community_detection()
    communities = []
    for row in results:
        communities.append({
            "file": row[0],
            "nodes": row[1],
            "edges": row[2],
        })
    return communities


def ascii_graph_stats(store: GraphStore) -> str:
    """Generate ASCII art summary of the graph."""
    stats = store.get_graph_stats()
    lines = [
        "╔══════════════════════════════════════════╗",
        "║         GraphLens — Code Graph           ║",
        "╠══════════════════════════════════════════╣",
        f"║  Nodes: {stats['total_nodes']:>6}                      ║",
        f"║  Edges: {stats['total_edges']:>6}                      ║",
        "╠══════════════════════════════════════════╣",
        "║  Node Types:                             ║",
    ]
    for ntype, count in list(stats["node_types"].items())[:5]:
        lines.append(f"║    {ntype:<15} {count:>4}                 ║")
    lines.append("╠══════════════════════════════════════════╣")
    lines.append("║  Edge Types:                             ║")
    for etype, count in list(stats["edge_types"].items())[:5]:
        lines.append(f"║    {etype:<15} {count:>4}                 ║")
    lines.append("╚══════════════════════════════════════════╝")
    return "\n".join(lines)
