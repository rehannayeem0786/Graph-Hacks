"""
FalkorDB Graph Store — the context layer for GraphLens.

Stores the parsed code graph in FalkorDB and provides:
- Cypher queries for the agent
- Graph algorithm tools (PageRank, shortest path, centrality)
- Multi-hop traversal for impact analysis
"""

from falkordb import FalkorDB

from src.config import (
    FALKORDB_HOST, FALKORDB_PORT, FALKORDB_GRAPH_NAME,
    FALKORDB_PASSWORD, FALKORDB_USERNAME, FALKORDB_SSL,
)
from src.parser import ParseResult


class GraphStore:
    """Manages the FalkorDB graph for code intelligence."""

    def __init__(self, host: str = None, port: int = None, graph_name: str = None,
                 password: str = None, ssl: bool = None, username: str = None):
        self.host = host or FALKORDB_HOST
        self.port = port or FALKORDB_PORT
        self.graph_name = graph_name or FALKORDB_GRAPH_NAME
        self.password = password if password is not None else FALKORDB_PASSWORD
        self.username = username if username is not None else FALKORDB_USERNAME
        self.ssl = ssl if ssl is not None else FALKORDB_SSL

        connect_kwargs = {"host": self.host, "port": self.port}
        if self.password:
            connect_kwargs["password"] = self.password
        if self.username:
            connect_kwargs["username"] = self.username
        if self.ssl:
            connect_kwargs["ssl"] = True
            connect_kwargs["ssl_cert_reqs"] = None

        self.client = FalkorDB(**connect_kwargs)
        self.graph = self.client.select_graph(self.graph_name)

    def ingest(self, parse_result: ParseResult) -> dict:
        """Ingest parsed code graph into FalkorDB with batch optimization."""
        from collections import defaultdict
        stats = {"nodes_created": 0, "edges_created": 0}

        # 1. Group nodes by type for fast batch UNWIND
        nodes_by_type = defaultdict(list)
        for node in parse_result.nodes:
            d = node.to_dict()
            ntype = d.pop("type", "Node")
            nodes_by_type[ntype].append(d)

        for ntype, items in nodes_by_type.items():
            for i in range(0, len(items), 50):
                batch = items[i:i + 50]
                query = f"UNWIND $batch AS item MERGE (n:{ntype} {{id: item.id}}) SET n += item"
                try:
                    self.graph.query(query, {"batch": batch})
                    stats["nodes_created"] += len(batch)
                except Exception:
                    for item in batch:
                        try:
                            self.graph.query(f"MERGE (n:{ntype} {{id: $id}}) SET n += $props", {"id": item["id"], "props": item})
                            stats["nodes_created"] += 1
                        except Exception:
                            pass

        # 2. Group edges by type for fast batch UNWIND
        edges_by_type = defaultdict(list)
        for edge in parse_result.edges:
            d = edge.to_dict()
            etype = d.pop("type", "RELATES_TO")
            edges_by_type[etype].append(d)

        for etype, items in edges_by_type.items():
            for i in range(0, len(items), 50):
                batch = items[i:i + 50]
                query = (
                    f"UNWIND $batch AS item "
                    f"MATCH (a {{id: item.source}}), (b {{id: item.target}}) "
                    f"MERGE (a)-[r:{etype} {{line: item.line}}]->(b)"
                )
                try:
                    self.graph.query(query, {"batch": batch})
                    stats["edges_created"] += len(batch)
                except Exception:
                    for item in batch:
                        try:
                            self.graph.query(
                                f"MATCH (a {{id: $source}}), (b {{id: $target}}) "
                                f"MERGE (a)-[r:{etype} {{line: $line}}]->(b)",
                                item
                            )
                            stats["edges_created"] += 1
                        except Exception:
                            pass
        return stats

    def query(self, cypher: str, params: dict = None) -> list:
        """Execute a raw Cypher query."""
        result = self.graph.query(cypher, params or {})
        return result.result_set

    def find_dependencies(self, module_name: str, depth: int = 3) -> list:
        """Find all dependencies of a module up to N hops."""
        cypher = f"""
        MATCH path = (m)-[:IMPORTS*1..{depth}]->(dep)
        WHERE m.name = $name
        RETURN m.name AS source, [n IN nodes(path) | n.name] AS chain,
               length(path) AS hops
        ORDER BY hops
        """
        return self.query(cypher, {"name": module_name})

    def impact_analysis(self, node_name: str, direction: str = "downstream") -> list:
        """Multi-hop impact analysis: what breaks if this changes?"""
        if direction == "downstream":
            cypher = """
            MATCH path = (n)-[:CALLS|IMPORTS|USES*1..5]->(affected)
            WHERE n.name = $name
            RETURN DISTINCT affected.name AS affected_node,
                   affected.file AS file,
                   length(path) AS impact_distance,
                   [r IN relationships(path) | type(r)] AS path_types
            ORDER BY impact_distance
            """
        else:
            cypher = """
            MATCH path = (affected)-[:CALLS|IMPORTS|USES*1..5]->(n)
            WHERE n.name = $name
            RETURN DISTINCT affected.name AS affected_by,
                   affected.file AS file,
                   length(path) AS distance,
                   [r IN relationships(path) | type(r)] AS path_types
            ORDER BY distance
            """
        return self.query(cypher, {"name": node_name})

    def get_graph_stats(self) -> dict:
        """Get overview statistics of the code graph."""
        node_count = self.query("MATCH (n) RETURN count(n)")[0][0]
        edge_count = self.query("MATCH ()-[r]->() RETURN count(r)")[0][0]
        node_types = self.query(
            "MATCH (n) RETURN DISTINCT labels(n)[0] AS type, count(n) AS cnt ORDER BY cnt DESC"
        )
        edge_types = self.query(
            "MATCH ()-[r]->() RETURN DISTINCT type(r) AS type, count(r) AS cnt ORDER BY cnt DESC"
        )
        return {
            "total_nodes": node_count,
            "total_edges": edge_count,
            "node_types": {row[0]: row[1] for row in node_types},
            "edge_types": {row[0]: row[1] for row in edge_types},
        }

    def find_shortest_path(self, source_name: str, target_name: str) -> list:
        """Find the shortest path between two nodes using native FalkorDB Cypher."""
        cypher = """
        MATCH (a), (b)
        WHERE (a.name = $source OR a.id = $source) AND (b.name = $target OR b.id = $target)
        WITH shortestPath((a)-[*..10]-(b)) AS path
        RETURN [n IN nodes(path) | n.name] AS path_nodes,
               [r IN relationships(path) | type(r)] AS path_edges,
               length(path) AS path_length
        ORDER BY length(path) ASC
        LIMIT 1
        """
        return self.query(cypher, {"source": source_name, "target": target_name})

    def pagerank(self, limit: int = 10) -> list:
        """Find the most important nodes via degree centrality."""
        cypher = f"""
        MATCH (n)
        WHERE any(l IN labels(n) WHERE l IN ['Class', 'Function', 'Method', 'Module'])
        OPTIONAL MATCH (n)<-[r]-(other)
        WITH n, count(r) AS in_degree
        OPTIONAL MATCH (n)-[r2]->(other2)
        WITH n, in_degree, count(r2) AS out_degree
        RETURN n.name AS name, labels(n)[0] AS type, n.file AS file,
               in_degree, out_degree,
               (in_degree * 2 + out_degree) AS importance_score
        ORDER BY importance_score DESC
        LIMIT {limit}
        """
        return self.query(cypher)

    def community_detection(self) -> list:
        """Detect communities/clusters in the code graph."""
        cypher = """
        MATCH (n)-[r]-(m)
        WHERE n.file = m.file AND n.file <> ''
        RETURN n.file AS file, count(DISTINCT n) AS node_count,
               count(r) AS edge_count
        ORDER BY node_count DESC
        """
        return self.query(cypher)

    def trace_decision(self, entity_name: str) -> list:
        """Trace all connections to/from an entity."""
        cypher = """
        MATCH path = (n)-[*1..4]-(connected)
        WHERE n.name = $name
        RETURN DISTINCT connected.name AS connected_to,
               connected.type AS type,
               [r IN relationships(path) | type(r)] AS via,
               length(path) AS distance
        ORDER BY distance
        LIMIT 50
        """
        return self.query(cypher, {"name": entity_name})

    def clear(self):
        """Clear the entire graph."""
        self.graph.query("MATCH (n) DETACH DELETE n")

    def get_schema(self) -> str:
        """Get the graph schema description."""
        node_labels = self.query("MATCH (n) RETURN DISTINCT labels(n)[0] AS label")
        rel_types = self.query("MATCH ()-[r]->() RETURN DISTINCT type(r) AS type")
        labels = [r[0] for r in node_labels if r[0]]
        types = [r[0] for r in rel_types if r[0]]
        return f"Node labels: {labels}\nRelationship types: {types}"
