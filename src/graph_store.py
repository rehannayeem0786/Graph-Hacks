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


_RESOLVED_SSL = None


class GraphStore:
    """Manages the FalkorDB graph for code intelligence."""

    def __init__(self, host: str = None, port: int = None, graph_name: str = None,
                 password: str = None, ssl: bool = None, username: str = None):
        global _RESOLVED_SSL
        self.host = host or FALKORDB_HOST
        self.port = port or FALKORDB_PORT
        self.graph_name = graph_name or FALKORDB_GRAPH_NAME
        self.password = password if password is not None else FALKORDB_PASSWORD
        self.username = username if username is not None else FALKORDB_USERNAME
        
        target_ssl = ssl if ssl is not None else FALKORDB_SSL
        if _RESOLVED_SSL is not None and ssl is None:
            target_ssl = _RESOLVED_SSL

        connect_kwargs = {
            "host": self.host,
            "port": self.port,
            "socket_connect_timeout": 3.0,
            "socket_timeout": 5.0,
        }
        if self.password:
            connect_kwargs["password"] = self.password
        if self.username:
            connect_kwargs["username"] = self.username

        ssl_candidates = [target_ssl, False] if target_ssl else [False]
        for use_ssl in ssl_candidates:
            opts = dict(connect_kwargs)
            opts["ssl"] = use_ssl
            if use_ssl:
                opts["ssl_cert_reqs"] = "none"
            try:
                candidate_client = FalkorDB(**opts)
                candidate_graph = candidate_client.select_graph(self.graph_name)
                candidate_graph.query("RETURN 1")
                self.client = candidate_client
                self.graph = candidate_graph
                self.ssl = use_ssl
                _RESOLVED_SSL = use_ssl
                break
            except Exception:
                continue

        if not hasattr(self, "client"):
            opts = dict(connect_kwargs)
            opts["ssl"] = target_ssl
            if target_ssl:
                opts["ssl_cert_reqs"] = "none"
            self.client = FalkorDB(**opts)
            self.graph = self.client.select_graph(self.graph_name)
            self.ssl = target_ssl

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
        """Find the shortest path between two nodes.

        Tries native directed shortestPath first, then falls back to a Python
        BFS over an undirected adjacency view — required because FalkorDB does
        not support undirected shortestPath traversals.

        Rows: [node_names, rel_types, length, directions] where each direction
        is 'fwd' (edge follows path direction) or 'rev' (edge is reversed).
        """
        for cypher, reverse in (
            ("""MATCH (a), (b)
            WHERE (a.name = $source OR a.id = $source) AND (b.name = $target OR b.id = $target)
            WITH shortestPath((a)-[*..10]->(b)) AS path
            WHERE path IS NOT NULL
            RETURN [n IN nodes(path) | n.name] AS path_nodes,
                   [r IN relationships(path) | type(r)] AS path_edges,
                   length(path) AS path_length
            LIMIT 1""", False),
            ("""MATCH (a), (b)
            WHERE (a.name = $source OR a.id = $source) AND (b.name = $target OR b.id = $target)
            WITH shortestPath((b)-[*..10]->(a)) AS path
            WHERE path IS NOT NULL
            RETURN [n IN nodes(path) | n.name] AS path_nodes,
                   [r IN relationships(path) | type(r)] AS path_edges,
                   length(path) AS path_length
            LIMIT 1""", True),
        ):
            try:
                res = self.query(cypher, {"source": source_name, "target": target_name})
                if res and len(res) > 0 and res[0][0]:
                    nodes, rels = res[0][0], res[0][1]
                    if reverse:
                        nodes, rels = list(reversed(nodes)), list(reversed(rels))
                    return [[nodes, rels, len(rels), ["fwd" if not reverse else "rev"] * len(rels)]]
            except Exception:
                continue

        # ── Undirected BFS fallback (FalkorDB lacks undirected shortestPath) ──
        try:
            edges = self.query(
                "MATCH (a)-[r]->(b) RETURN a.id, a.name, labels(a)[0], "
                "type(r), b.id, b.name, labels(b)[0]")
        except Exception:
            return []
        if not edges:
            return []

        from collections import defaultdict, deque
        _pref = {"Function": 0, "Class": 0, "Method": 1, "Module": 1,
                 "ExternalModule": 2, "Call": 3}
        adj, names, prefs = defaultdict(list), {}, {}
        for a_id, a_name, a_lbl, rel, b_id, b_name, b_lbl in edges:
            names[a_id] = a_name or a_id
            names[b_id] = b_name or b_id
            prefs[a_id] = _pref.get(a_lbl, 2)
            prefs[b_id] = _pref.get(b_lbl, 2)
            adj[a_id].append((b_id, rel, True))
            adj[b_id].append((a_id, rel, False))

        sources = sorted([nid for nid in names if nid == source_name or names[nid] == source_name],
                         key=lambda x: prefs.get(x, 2))
        targets = {nid for nid in names if nid == target_name or names[nid] == target_name}
        if not sources or not targets:
            return []

        parent = {s: None for s in sources}
        q = deque(sources)
        found = None
        while q:
            cur = q.popleft()
            if cur in targets:
                found = cur
                break
            for nxt, rel, fwd in adj[cur]:
                if nxt not in parent:
                    parent[nxt] = (cur, rel, fwd)
                    q.append(nxt)
        if found is None:
            return []

        node_ids, rel_types, directions = [], [], []
        cur = found
        while cur is not None:
            node_ids.append(cur)
            entry = parent[cur]
            if entry is not None:
                _prev, rel, fwd = entry
                rel_types.append(rel)
                directions.append("fwd" if fwd else "rev")
            cur = entry[0] if entry else None
        node_ids.reverse()
        rel_types.reverse()
        directions.reverse()
        return [[[names.get(nid, nid) for nid in node_ids], rel_types,
                  len(rel_types), directions]]

    def link_definitions(self) -> dict:
        """Idempotently link synthetic nodes to real definitions.

        - Call -(RESOLVES_TO)-> unique Function/Method/Class with same name
        - ExternalModule -(ALIAS_OF)-> internal Module (src.parser -> parser.py)

        Safe to run repeatedly (MERGE-based). Returns link counts.
        """
        stats = {"resolved_calls": 0, "aliased_imports": 0}
        try:
            rows = self.query("""
            MATCH (c:Call)
            WITH c, c.name AS nm
            MATCH (d) WHERE d.name = nm AND (d:Function OR d:Method OR d:Class)
            WITH c, collect(DISTINCT d) AS defs
            WHERE size(defs) = 1
            WITH c, defs[0] AS d
            MERGE (c)-[:RESOLVES_TO]->(d)
            RETURN count(*) AS linked
            """)
            stats["resolved_calls"] = rows[0][0] if rows else 0
        except Exception:
            pass

        try:
            modules = self.query("MATCH (m:Module) RETURN m.id, m.file")
            externals = self.query(
                "MATCH (e:ExternalModule) WHERE NOT (e)-[:ALIAS_OF]->() "
                "RETURN e.id, e.name")
            file_to_id = {row[1]: row[0] for row in modules if row[1]}
            pairs = []
            for eid, ename in externals:
                if not ename:
                    continue
                candidates = [ename]
                if "." in ename:
                    candidates.append(ename.split(".", 1)[1])
                for cand in candidates:
                    mid = file_to_id.get(cand + ".py")
                    if mid:
                        pairs.append([eid, mid])
                        break
            if pairs:
                self.query(
                    "UNWIND $pairs AS p "
                    "MATCH (a {id: p[0]}), (b {id: p[1]}) "
                    "MERGE (a)-[:ALIAS_OF]->(b)",
                    {"pairs": pairs})
            stats["aliased_imports"] = len(pairs)
        except Exception:
            pass
        return stats

    def suggest_entities(self, name: str, limit: int = 3) -> list:
        """Find entities with similar names (did-you-mean helper)."""
        safe = str(name).replace("'", "").replace('"', "")[:80]
        try:
            rows = self.query(
                f"MATCH (n) WHERE toLower(n.name) CONTAINS toLower('{safe}') "
                f"RETURN DISTINCT n.name LIMIT {int(limit)}")
            return [r[0] for r in rows]
        except Exception:
            return []

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
