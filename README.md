<div align="center">

# 🔍 GraphLens

### AI Code Intelligence Agent Powered by FalkorDB Knowledge Graphs

**Winner-grade submission for [Graph Hacks 2026](https://www.wemakedevs.org/hackathons/falkordb)**

*Turn any codebase into a queryable knowledge graph. Ask questions. Get explainable answers.*

[![Tests](https://img.shields.io/badge/tests-19%2F19%20passing-brightgreen?style=for-the-badge)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![FalkorDB](https://img.shields.io/badge/FalkorDB-powered-orange?style=for-the-badge)](https://falkordb.com)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

[Quick Start](#-quick-start) | [Features](#-features) | [Architecture](#-architecture) | [API](#-api-reference)

</div>

---

## 🎯 The Problem

Developers can't answer critical questions about their codebase:
- *"What breaks if I change this module?"*
- *"What's the most critical code in this project?"*
- *"How does feature X connect to module Y?"*

Existing tools give flat file lists. **GraphLens gives you a graph.**

## 💡 The Solution

```
Codebase -> AST Parser -> FalkorDB Graph -> AI Agent -> Explained Answers
```

GraphLens parses any Python codebase into a **knowledge graph** in FalkorDB, then uses an AI agent to reason over it with multi-hop traversals. Every answer is backed by an **explainable graph path**.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **AI Agent** | LLM-powered tool selection with multi-hop reasoning |
| 📊 **Graph Algorithms** | PageRank, shortest path, community detection, impact |
| 🌐 **Interactive Dashboard** | D3.js force-directed graph with search & zoom |
| 🔌 **MCP Server** | Model Context Protocol for any compatible agent |
| 🧠 **Agent Memory** | Persistent facts across sessions (Track 02) |
| 🤝 **Multi-Agent Bus** | Task queue, handoffs, coordination (Track 02) |
| 📝 **Explainable** | Every answer shows the exact graph path |

## 🏆 Why This Wins

| Hackathon Requirement | GraphLens Delivers |
|---|---|
| Graph shapes agent behavior | Every answer from Cypher queries, not hallucination |
| Multi-hop reasoning | Agent traces A->CALLS->B->IMPORTS->C chains |
| Graph algorithms as tools | PageRank, shortest path, communities, impact |
| Explainable results | Graph path shown with every answer |
| MCP-style tool selection | Full MCP server with 7 graph tools |
| FalkorDB as primary DB | 100% of context lives in FalkorDB |

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <this-repo> && cd graphlens
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start FalkorDB
docker run -p 6379:6379 falkordb/falkordb:latest

# 4. Configure
copy .env.example .env
# Edit .env with your OpenRouter API key

# 5. Ingest a codebase
python -m src.cli ingest ./src

# 6. Ask questions!
python -m src.cli ask "What is the most critical module?"

# 7. Launch dashboard
python -m src.cli serve
# Open http://localhost:8000
```

## 🏗 Architecture

```
+---------------------------------------------------+
|              GraphLens AI Agent                    |
|  (LLM + Tool Selection + Multi-hop Reasoning)     |
+---------------------------------------------------+
|              FalkorDB Graph Store                  |
|  (Cypher, PageRank, Shortest Path, Communities)   |
+---------------------------------------------------+
|           AST Parser (Python)                      |
|  (Deterministic extraction, every edge explained)  |
+---------------------------------------------------+
|              Your Codebase (.py)                   |
+---------------------------------------------------+
```

## 🛠 Agent Tools

| Tool | Description |
|------|-------------|
| `impact_analysis` | Multi-hop blast radius of code changes |
| `find_dependencies` | Module dependency chains to depth N |
| `find_shortest_path` | Shortest path between any two entities |
| `pagerank` | Most critical/connected code nodes |
| `trace_decision` | All connections of an entity (4 hops) |
| `community_detection` | Code clusters by file/module |
| `cypher` | Raw Cypher for advanced queries |

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/ingest` | Parse codebase into graph |
| `POST` | `/ask` | Ask the AI agent |
| `GET` | `/stats` | Graph statistics |
| `GET` | `/graph` | Full graph (D3.js JSON) |
| `GET` | `/graph/search?q=` | Search nodes |
| `GET` | `/graph/path?source=&target=` | Shortest path |
| `GET` | `/graph/impact?name=&direction=` | Impact analysis |
| `GET` | `/graph/communities` | Community detection |
| `GET` | `/graph/pagerank?limit=` | Top nodes by importance |

Interactive docs: `http://localhost:8000/docs`

## 🤖 LLM Providers

| Provider | Config | Notes |
|----------|--------|-------|
| **OpenRouter** (default) | `LLM_PROVIDER=openrouter` | 200+ models |
| **Groq** | `LLM_PROVIDER=groq` | Fast inference |

Get keys: [OpenRouter](https://openrouter.ai/keys) | [Groq](https://console.groq.com/keys)

## 🔌 MCP Server

```bash
python -m src.mcp_server
```

Any MCP-compatible agent (Claude, Cursor, etc.) can call all 7 graph tools via JSON-RPC.

## 🧠 Agent Memory (Track 02)

```python
from src.memory import AgentMemory
memory = AgentMemory(store, session_id="user_123")
memory.remember("config.py is critical", "architecture")
context = memory.get_context()  # Fed into next session
```

## 🤝 Multi-Agent Coordination (Track 02)

```python
from src.multi_agent import AgentBus
bus = AgentBus(store)
bus.register("reviewer", ["impact_analysis", "pagerank"])
task_id = bus.create_task("Review parser.py", priority=9)
task = bus.claim_task()
bus.complete_task(task_id, "No issues found")
bus.handoff("security-agent", "Focus on injection vectors")
```

## 🧪 Testing

```bash
python -m pytest tests/ -v
# 19/19 passing with FalkorDB running
```

## 📝 Track Alignment

### Track 01: Agents That Act on Connected Data
- Multi-hop reasoning via CALLS, IMPORTS, INHERITS edges
- 7 Cypher-backed graph tools
- MCP server for tool selection
- Explainable graph paths in every answer

### Track 02: Agent Memory and Coordination
- Persistent memory in FalkorDB
- Session isolation via graph names
- Multi-agent task queue with handoffs

## 📁 Project Structure

```
src/
  parser.py          # AST-based code graph extraction
  graph_store.py     # FalkorDB operations + algorithms
  agent.py           # AI agent with tool-calling loop
  mcp_server.py      # MCP tool server
  memory.py          # Persistent agent memory
  multi_agent.py     # Multi-agent coordination
  visualization.py   # D3.js + ASCII visualizations
  server.py          # FastAPI REST API
  cli.py             # CLI interface
  config.py          # Configuration
static/
  index.html         # Interactive dashboard
  app.js             # D3.js visualization
tests/               # 19 tests
demo.py              # Full demo script
docker-compose.yml   # One-command deployment
```

## 🔑 Key Differentiators

1. **No vector store** - Pure structural graph
2. **Explainable** - Every answer shows the graph path
3. **MCP-native** - Any MCP agent can use our tools
4. **Memory in graph** - Persistent across sessions
5. **Interactive viz** - D3.js force-directed graph
6. **Production API** - Full REST with error handling

## 📄 License

MIT License

---

<div align="center">

*Built for Graph Hacks 2026 | Powered by FalkorDB*

</div>
