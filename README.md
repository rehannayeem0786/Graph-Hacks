<div align="center">

# 🔍 GraphLens

### AI Code Intelligence Agent Powered by FalkorDB Knowledge Graphs

**Built for [Graph Hacks 2026](https://www.wemakedevs.org/hackathons/falkordb)**

*Turn any codebase into a queryable knowledge graph. Ask questions. Get explainable, graph-backed answers.*

[![Tests](https://img.shields.io/badge/tests-43%2F43%20passing-brightgreen?style=for-the-badge)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![FalkorDB](https://img.shields.io/badge/FalkorDB-powered-orange?style=for-the-badge)](https://falkordb.com)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

[Quick Start](#-quick-start) | [Features](#-features) | [Architecture](#-architecture) | [API](#-api-reference) | [Tracks](#-track-alignment)

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
Codebase → AST Parser → FalkorDB Graph → AI Agent → Explained Answers
                              ↕
                    Memory + Multi-Agent (Track 02)
```

GraphLens parses any Python codebase into a **knowledge graph** in FalkorDB, then uses an AI agent to reason over it with multi-hop Cypher traversals. Every answer is backed by an **explainable graph path**. The agent remembers insights across sessions and coordinates with other agents through graph state.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **AI Agent** | LLM-powered tool selection with multi-hop graph reasoning |
| 📊 **Graph Algorithms** | PageRank, shortest path, community detection, impact analysis |
| 🌐 **Premium Dashboard** | D3.js force-directed graph with glassmorphism design |
| ⚡ **SSE Streaming** | Real-time word-by-word agent responses |
| 🔮 **Graph Path Animation** | Answers animate the traversal path on the graph |
| 🔌 **MCP Server** | Model Context Protocol for any compatible agent |
| 🧠 **Agent Memory** | Persistent facts across sessions in FalkorDB (Track 02) |
| 🤝 **Multi-Agent Bus** | Task queue, handoffs, coordination in graph (Track 02) |
| ⚡ **Cypher Playground** | Run raw Cypher queries from the browser |
| 📝 **Explainable** | Every answer shows the exact graph path |

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
docker run -d -p 6379:6379 falkordb/falkordb:latest

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
┌─────────────────────────────────────────────────────────────┐
│                    GraphLens Dashboard                       │
│  (D3.js · Agent Chat · Memory · Multi-Agent · Cypher)       │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI REST + SSE Server                  │
├─────────────────┬───────────────────┬───────────────────────┤
│  AI Agent       │  Agent Memory     │  Multi-Agent Bus      │
│  (LLM + Tools)  │  (FalkorDB)       │  (FalkorDB)           │
├─────────────────┴───────────────────┴───────────────────────┤
│                  FalkorDB Graph Store                        │
│  (Cypher · PageRank · Shortest Path · Communities)          │
├─────────────────────────────────────────────────────────────┤
│              AST Parser (Deterministic Extraction)           │
└─────────────────────────────────────────────────────────────┘
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
| `GET` | `/ask/stream` | SSE streaming agent response |
| `GET` | `/stats` | Graph statistics (with query time ms) |
| `GET` | `/graph` | Full graph (D3.js JSON) |
| `GET` | `/graph/schema` | Live graph data model & relationship patterns |
| `GET` | `/graph/search?q=` | Search nodes |
| `GET` | `/graph/path?source=&target=` | Shortest path |
| `GET` | `/graph/impact?name=&direction=` | Impact analysis |
| `GET` | `/graph/communities` | Community detection |
| `GET` | `/graph/pagerank?limit=` | Top nodes by importance |
| `GET` | `/graph/node/{name}` | Node detail + connections |
| `POST` | `/graph/cypher` | Cypher playground |
| `GET` | `/memory` | List agent memories |
| `POST` | `/memory` | Store a memory fact |
| `POST` | `/multi-agent/analyze` | Multi-agent demo |
| `GET` | `/multi-agent/state` | Shared agent state |

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

## 📋 Track Alignment

### Track 01: Agents That Act on Connected Data
- Multi-hop reasoning via CALLS, IMPORTS, INHERITS edges
- 7 Cypher-backed graph tools
- MCP server for tool selection
- Explainable graph paths in every answer
- Graph path animation on D3 visualization
- SSE streaming agent responses

### Track 02: Agent Memory and Coordination
- Persistent memory in FalkorDB — agent auto-remembers insights
- Memory recalled automatically in next session
- Multi-agent task queue with priority-based claiming
- Agent-to-agent handoffs through graph state
- Live demo: 3 agents coordinate through FalkorDB

## 📁 Project Structure

```
src/
  parser.py          # AST-based code graph extraction
  graph_store.py     # FalkorDB operations + algorithms + schema
  agent.py           # AI agent with memory-integrated tool loop
  mcp_server.py      # MCP tool server (7 tools)
  memory.py          # Persistent agent memory (Track 02)
  multi_agent.py     # Multi-agent coordination (Track 02)
  visualization.py   # D3.js + ASCII visualizations
  server.py          # FastAPI REST + SSE (19 endpoints)
  cli.py             # CLI interface
  config.py          # Configuration
static/
  index.html         # Premium glassmorphism dashboard (5 tabs)
  app.js             # Frontend: streaming, animation, memory, schema
tests/               # 43 automated tests (100% pass)
```

## 🔑 Key Differentiators

1. **Graph is central, not decorative** — Remove FalkorDB and nothing works
2. **Explainable** — Every answer shows the graph path
3. **Memory IS the graph** — Agent facts stored as FalkorDB nodes
4. **Multi-agent in the graph** — Tasks, handoffs, state all through Cypher
5. **MCP-native** — Any MCP agent can use our tools
6. **Cypher playground** — Explore the graph yourself
7. **SSE streaming** — Real-time responses with graph animation
8. **Premium UI** — Glassmorphism, micro-animations, 5-tab layout

## 🧪 Testing

```bash
python -m pytest tests/ -v
# 43/43 passing with FalkorDB running
```

## 🤖 AI Coding Assistant Disclosure

AI coding assistants were used during development for code generation and debugging. All architecture decisions, graph modeling, agent design, and technical choices were made by the developer. The developer understands and can explain every component of this codebase.

## 📄 License

MIT License

---

<div align="center">

*Built for Graph Hacks 2026 | Powered by FalkorDB*

</div>
