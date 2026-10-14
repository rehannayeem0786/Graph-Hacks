"""
Multi-Agent Coordination — Track 02: agents share state via FalkorDB.

Implements a lightweight agent bus where multiple GraphLens agents
can coordinate through the shared graph:
- Shared task queue (nodes with status)
- Agent registration and heartbeat
- Handoff: one agent passes context to another
- Shared state: all agents read/write the same graph

This demonstrates "Shared state and handoffs between agents"
and "High-concurrency reads and writes" from Track 02.
"""

import json
import time
import uuid
from src.graph_store import GraphStore


class AgentBus:
    """Coordination bus for multiple agents sharing a FalkorDB graph."""

    def __init__(self, store: GraphStore):
        self.store = store
        self.agent_id = f"agent:{uuid.uuid4().hex[:8]}"

    def register(self, agent_name: str, capabilities: list = None):
        """Register this agent in the shared graph."""
        cypher = """
        MERGE (a:Agent {id: $id})
        SET a.name = $name, a.capabilities = $caps,
            a.registered_at = $ts, a.status = 'active'
        """
        self.store.query(cypher, {
            "id": self.agent_id,
            "name": agent_name,
            "caps": json.dumps(capabilities or []),
            "ts": time.time(),
        })
        return self.agent_id

    def heartbeat(self):
        """Update agent heartbeat timestamp."""
        cypher = """
        MATCH (a:Agent {id: $id})
        SET a.last_heartbeat = $ts, a.status = 'active'
        """
        self.store.query(cypher, {"id": self.agent_id, "ts": time.time()})

    def create_task(self, description: str, priority: int = 5,
                    required_capability: str = None) -> str:
        """Create a task in the shared queue."""
        task_id = f"task:{uuid.uuid4().hex[:8]}"
        cypher = """
        CREATE (t:Task {
            id: $id, description: $desc, priority: $priority,
            required_capability: $cap, status: 'pending',
            created_at: $ts, created_by: $creator
        })
        """
        self.store.query(cypher, {
            "id": task_id, "desc": description,
            "priority": priority, "cap": required_capability or "",
            "ts": time.time(), "creator": self.agent_id,
        })
        return task_id

    def claim_task(self) -> dict:
        """Claim the highest-priority pending task."""
        cypher = """
        MATCH (t:Task {status: 'pending'})
        WHERE t.required_capability = '' OR t.required_capability IS NULL
        RETURN t.id, t.description, t.priority
        ORDER BY t.priority DESC
        LIMIT 1
        """
        results = self.store.query(cypher)
        if not results:
            return {}
        task_id = results[0][0]
        claim_cypher = """
        MATCH (t:Task {id: $id, status: 'pending'})
        SET t.status = 'in_progress', t.claimed_by = $agent, t.claimed_at = $ts
        """
        self.store.query(claim_cypher, {
            "id": task_id, "agent": self.agent_id, "ts": time.time(),
        })
        return {"id": task_id, "description": results[0][1], "priority": results[0][2]}

    def complete_task(self, task_id: str, result: str):
        """Mark a task as complete with its result."""
        cypher = """
        MATCH (t:Task {id: $id})
        SET t.status = 'complete', t.result = $result, t.completed_at = $ts
        """
        self.store.query(cypher, {"id": task_id, "result": result, "ts": time.time()})

    def handoff(self, target_agent_name: str, context: str):
        """Hand off context to another agent."""
        handoff_id = f"handoff:{uuid.uuid4().hex[:8]}"
        cypher = """
        CREATE (h:Handoff {
            id: $id, from_agent: $from_id, to_agent: $to_name,
            context: $ctx, created_at: $ts, status: 'pending'
        })
        """
        self.store.query(cypher, {
            "id": handoff_id, "from_id": self.agent_id,
            "to_name": target_agent_name, "ctx": context, "ts": time.time(),
        })
        return handoff_id

    def get_handoffs(self) -> list:
        """Get pending handoffs for this agent."""
        cypher = """
        MATCH (h:Handoff {status: 'pending'})
        RETURN h.id, h.from_agent, h.context, h.created_at
        ORDER BY h.created_at
        """
        return self.store.query(cypher)

    def list_agents(self) -> list:
        """List all registered agents."""
        cypher = """
        MATCH (a:Agent)
        WHERE a.status = 'active'
        RETURN a.id, a.name, a.capabilities, a.last_heartbeat
        """
        return self.store.query(cypher)

    def get_shared_state(self) -> dict:
        """Get the current shared state summary."""
        tasks = self.store.query(
            "MATCH (t:Task) RETURN t.status, count(t) ORDER BY t.status"
        )
        agents = self.store.query(
            "MATCH (a:Agent {status: 'active'}) RETURN count(a)"
        )
        handoffs = self.store.query(
            "MATCH (h:Handoff {status: 'pending'}) RETURN count(h)"
        )
        return {
            "tasks_by_status": {r[0]: r[1] for r in tasks},
            "active_agents": agents[0][0] if agents else 0,
            "pending_handoffs": handoffs[0][0] if handoffs else 0,
        }
