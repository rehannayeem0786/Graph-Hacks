# GraphLens — FalkorDB-Powered AI Code Intelligence

## Graph Hacks 2026 Submission

**Team:** Solo
**Tracks:** Track 01 (Agents That Act on Connected Data) + Track 02 (Agent Memory and Coordination)

---

## 🎯 The Problem

Developers can't answer critical questions about their codebase:
- "What breaks if I change this module?"
- "What's the most critical code in this project?"
- "How does feature X connect to module Y?"

Existing tools give flat file lists. **GraphLens gives you a graph.**

## 💡 The Solution

GraphLens parses any Python codebase into a **knowledge graph** stored in FalkorDB, then uses an AI agent (Groq/OpenRouter) to reason over it with multi-hop traversals.

```
Codebase → AST Parser → FalkorDB Graph → AI Agent → Explained Answers
```

## 🕵️ Track 01: Agents That Act on Connected Data

| Requirement | Implementation |
|---|---|
| Multi-hop reasoning | Agent follows 1-5 hop paths through CALLS, IMPORTS, INHERITS edges |
| Graph queries as agent tools | 7 Cypher-backed tools (PageRank, shortest path, impact, communities) |
| Tool selection through MCP | Full MCP server (`src/mcp_server.py`) exposing all tools via JSON-RPC |
| Actions based on graph | Impact analysis drives refactoring suggestions |
| Explainable results | Every answer shows: `A -[CALLS]-> B -[IMPORTS]-> C` |

## 🤖 Track 02: Agent Memory and Coordination

| Requirement | Implementation |
|---|---|
| Episodic/semantic memory | `AgentMemory` stores facts, decisions, reasoning paths in FalkorDB |
| Persistent history | Memory survives across sessions via graph persistence |
| Shared state | `AgentBus` — task queue, handoffs, shared graph state |
| Handoffs between agents | `bus.handoff(target, context)` passes reasoning to next agent |
| High-concurrency R/W | All coordination via atomic Cypher MERGE/MATCH in FalkorDB |
| Per-user isolation | Separate graph names per user/tenant |

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Codebase   │────▶│  AST Parser  │────▶│   FalkorDB      │
│  (Python)   │     │  (src/parser)│     │  (Graph Store)  │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
┌─────────────┐     ┌──────────────┐     ┌────────▼────────┐
│  Web UI     │◀────│  FastAPI     │◀────│  AI Agent       │
│  (D3.js)   │     │  Server      │     │  (Groq/OR)      │
└─────────────┘     └──────────────┘     └─────────────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │  MCP Server     │
                                          │  (Tool Select)  │
                                          └─────────────────┘
```

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start FalkorDB
docker run -d -p 6379:6379 falkordb/falkordb:latest

# 3. Configure
cp .env.example .env
# Add your GROQ_API_KEY to .env

# 4. Ingest a codebase
python -m src.cli ingest ./src

# 5. Ask questions
python -m src.cli ask "What is the most critical module?"

# 6. Start web dashboard
python -m src.cli serve
# Open http://localhost:8000
```

## 📁 Project Structure

```
├── src/
│   ├── parser.py          # AST-based code graph extraction
│   ├── graph_store.py     # FalkorDB operations + algorithms
│   ├── agent.py           # AI agent with tool-calling loop
│   ├── mcp_server.py      # MCP tool selection server
│   ├── memory.py          # Persistent agent memory (Track 02)
│   ├── multi_agent.py     # Multi-agent coordination bus (Track 02)
│   ├── visualization.py   # D3.js + ASCII visualizations
│   ├── server.py          # FastAPI REST API
│   ├── cli.py             # CLI interface
│   └── config.py          # Configuration
├── static/
│   ├── index.html         # D3.js interactive graph UI
│   └── app.js             # Frontend logic
├── tests/                 # 19 tests (7 pass offline, 12 need FalkorDB)
├── demo.py                # Full demo script
├── docker-compose.yml     # One-command deployment
├── Dockerfile             # Container build
├── setup.ps1              # Windows setup automation
└── .github/workflows/     # CI with FalkorDB service container
```

## 🎬 Demo Flow (for video)

1. `python demo.py` — Shows full pipeline
2. `python -m src.cli serve` — Open dashboard at localhost:8000
3. Ask: "What breaks if I modify the parser?"
4. Show impact analysis with graph path explanation
5. Show MCP server: `python -m src.mcp_server`

## 🔑 Key Differentiators

1. **No vector store needed** — Pure structural graph extraction
2. **Every answer is explainable** — Shows the exact graph path
3. **MCP-native** — Any MCP-compatible agent can use our tools
4. **Memory in the graph** — Agent remembers across sessions
5. **Interactive visualization** — D3.js force-directed graph

---

*Built for Graph Hacks 2026 | Powered by FalkorDB*
