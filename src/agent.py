"""
GraphLens Agent — the AI brain that reasons over the code graph.
"""

import json
import httpx

from src.config import (
    LLM_PROVIDER, GROQ_API_KEY, GROQ_MODEL,
    OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL,
)
from src.graph_store import GraphStore

SYSTEM_PROMPT = """You are GraphLens, an expert code intelligence agent.
Tools (respond JSON {"tool":"...","args":{...}} or {"answer":"...","graph_path":"..."}):
- impact_analysis: {"name":"...","direction":"downstream|upstream"}
- find_dependencies: {"name":"...","depth":3}
- find_shortest_path: {"source":"...","target":"..."}
- pagerank: {"limit":10}
- trace_decision: {"name":"..."}
- community_detection: {}
- get_stats: {}
- cypher: {"query":"MATCH ..."}
RULES: Always use a tool first. Explain the GRAPH PATH. Show multi-hop: A-[CALLS]->B-[IMPORTS]->C."""


class GraphLensAgent:
    """AI Agent that reasons over the code knowledge graph."""

    def __init__(self, store: GraphStore):
        self.store = store
        self.history: list[dict] = []

    def ask(self, question: str) -> str:
        """Process a user question through the agent loop."""
        self.history.append({"role": "user", "content": question})
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"Schema: {self.store.get_schema()}"},
        ] + self.history[-10:]

        for _ in range(5):
            raw = self._llm_chat(messages)
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                self.history.append({"role": "assistant", "content": raw})
                return raw

            if "answer" in parsed:
                final = parsed["answer"]
                if "graph_path" in parsed:
                    final += f"\n\nGraph Path: {parsed['graph_path']}"
                self.history.append({"role": "assistant", "content": final})
                return final

            if "tool" in parsed:
                result = self._execute_tool(parsed["tool"], parsed.get("args", {}))
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": f"Tool result:\n{result}\nNow answer."})
                continue

        return "Agent reached maximum reasoning steps."

    def _execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a graph tool and return results as string."""
        try:
            if tool_name == "impact_analysis":
                rows = self.store.impact_analysis(
                    args.get("name", ""), args.get("direction", "downstream")
                )
            elif tool_name == "find_dependencies":
                rows = self.store.find_dependencies(
                    args.get("name", ""), args.get("depth", 3)
                )
            elif tool_name == "find_shortest_path":
                rows = self.store.find_shortest_path(
                    args.get("source", ""), args.get("target", "")
                )
            elif tool_name == "pagerank":
                rows = self.store.pagerank(args.get("limit", 10))
            elif tool_name == "trace_decision":
                rows = self.store.trace_decision(args.get("name", ""))
            elif tool_name == "community_detection":
                rows = self.store.community_detection()
            elif tool_name == "get_stats":
                return json.dumps(self.store.get_graph_stats(), indent=2)
            elif tool_name == "cypher":
                rows = self.store.query(args.get("query", ""))
            else:
                return f"Unknown tool: {tool_name}"
            return json.dumps(rows, indent=2, default=str)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def _llm_chat(self, messages: list[dict]) -> str:
        """Route to the configured LLM provider (Groq or OpenRouter)."""
        if LLM_PROVIDER == "groq":
            return self._groq_chat(messages)
        elif LLM_PROVIDER == "openrouter":
            return self._openrouter_chat(messages)
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Use 'groq' or 'openrouter'.")

    def _groq_chat(self, messages: list[dict]) -> str:
        try:
            resp = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={"model": GROQ_MODEL, "messages": messages, "temperature": 0.1},
                timeout=60.0,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            return json.dumps({"error": f"Groq API error {e.response.status_code}: {e.response.text[:200]}"})
        except httpx.RequestError as e:
            return json.dumps({"error": f"Groq connection error: {str(e)}"})

    def _openrouter_chat(self, messages: list[dict]) -> str:
        try:
            resp = httpx.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://github.com/graphlens",
                    "X-Title": "GraphLens",
                },
                json={"model": OPENROUTER_MODEL, "messages": messages, "temperature": 0.1},
                timeout=90.0,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            return json.dumps({"error": f"OpenRouter API error {e.response.status_code}: {e.response.text[:200]}"})
        except httpx.RequestError as e:
            return json.dumps({"error": f"OpenRouter connection error: {str(e)}"})