"""
Agent Memory Layer — Track 02 bonus: persistent memory across sessions.

Stores conversation history, decisions, and learned facts in FalkorDB
so the agent remembers across sessions.
"""

import json
import time
from src.graph_store import GraphStore


class AgentMemory:
    """Persistent agent memory stored in FalkorDB."""

    def __init__(self, store: GraphStore, session_id: str = "default"):
        self.store = store
        self.session_id = session_id

    def remember(self, fact: str, category: str = "general"):
        """Store a fact in memory."""
        cypher = """
        MERGE (m:Memory {id: $id})
        SET m.fact = $fact, m.category = $category,
            m.timestamp = $ts, m.session = $session
        """
        mem_id = f"memory:{self.session_id}:{int(time.time() * 1000)}"
        self.store.query(cypher, {
            "id": mem_id, "fact": fact,
            "category": category, "ts": time.time(),
            "session": self.session_id,
        })

    def recall(self, category: str = None, limit: int = 20) -> list:
        """Recall facts from memory."""
        if category:
            cypher = """
            MATCH (m:Memory)
            WHERE m.session = $session AND m.category = $category
            RETURN m.fact AS fact, m.timestamp AS ts
            ORDER BY m.timestamp DESC LIMIT $limit
            """
            return self.store.query(cypher, {
                "session": self.session_id,
                "category": category, "limit": limit,
            })
        else:
            cypher = """
            MATCH (m:Memory)
            WHERE m.session = $session
            RETURN m.fact AS fact, m.category AS category, m.timestamp AS ts
            ORDER BY m.timestamp DESC LIMIT $limit
            """
            return self.store.query(cypher, {
                "session": self.session_id, "limit": limit,
            })

    def remember_decision(self, question: str, answer: str, graph_path: str):
        """Store a decision with its reasoning path."""
        cypher = """
        CREATE (d:Decision {
            id: $id, question: $question, answer: $answer,
            graph_path: $path, timestamp: $ts, session: $session
        })
        """
        self.store.query(cypher, {
            "id": f"decision:{int(time.time() * 1000)}",
            "question": question, "answer": answer,
            "path": graph_path, "ts": time.time(),
            "session": self.session_id,
        })

    def get_context(self) -> str:
        """Get memory context for the agent prompt."""
        facts = self.recall(limit=10)
        if not facts:
            return ""
        context = "Previous session memory:\n"
        for f in facts:
            context += f"- {f[0]}\n"
        return context