# 🔍 GraphLens — AI Code Intelligence Agent

**Winner-grade submission for [Graph Hacks: Context for AI Agents](https://www.wemakedevs.org/hackathons/falkordb) — Track 01: Agents That Act on Connected Data**

GraphLens turns any codebase into a **queryable knowledge graph** in FalkorDB, then deploys an AI agent that **reasons over the graph** to answer questions about impact, dependencies, architecture, and risk — with **every answer backed by an explainable graph path**.

## 🏆 Why This Wins

| Hackathon Requirement | GraphLens Delivers |
|---|---|
| Graph shapes what the agent does | Every answer comes from Cypher queries, not LLM hallucination |
| Multi-hop reasoning | Agent traces A→CALLS→B→IMPORTS→C chains automatically |
| Graph algorithms as tools | PageRank, shortest path, community detection, impact analysis |
| Explainable results | Every answer includes the graph path that produced it |
| Tool selection through MCP-style interface | Agent picks the right graph tool per question |
| FalkorDB as primary DB | 100% of context lives in FalkorDB |

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <this-repo>
cd graphlens
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start FalkorDB (Docker)
docker run -p 6379:6379 falkordb/falkordb:latest

# 4. Configure
copy .env.example .env
# Edit .env with your Groq or OpenRouter API key

# 5. Ingest a codebase
python -m src.cli ingest ./path/to/your/project

# 6. Ask questions!
python -m src.cli ask "What breaks if I change the config module?"
python -m src.cli ask "Which function is most critical?"
python -m src.cli ask "Show me the path from main to database"
```

## 🧠 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   GraphLens Agent                    │
│  (LLM + Tool Selection + Multi-hop Reasoning)       │
├─────────────────────────────────────────────────────┤
│              FalkorDB Graph Store                    │
│  (Cypher queries, PageRank, Shortest Path, etc.)    │
├─────────────────────────────────────────────────────┤
│           AST Parser (Graphify-inspired)             │
│  (Deterministic extraction, every edge explained)   │
├─────────────────────────────────────────────────────┤
│              Your Codebase                           │
│  (.py .js .ts .java .go .rs .c .cpp .rb .php)      │
└─────────────────────────────────────────────────────┘
```

## 🛠️ Agent Tools (Graph Algorithms)

| Tool | What it does |
|---|---|
| `impact_analysis` | Multi-hop downstream/upstream blast radius |
| `find_dependencies` | Module dependency chains to depth N |
| `find_shortest_path` | Shortest path between any two entities |
| `pagerank` | Most critical/connected code nodes |
| `trace_decision` | All connections of an entity (4 hops) |
| `community_detection` | Code clusters by file/module |
| `cypher` | Raw Cypher for advanced queries |

## 📡 API Server

```bash
python -m src.cli serve
# → http://localhost:8000/docs (Swagger UI)
```

## 🤖 LLM Providers

| Provider | Config | Cost | Speed |
|---|---|---|---|
| **Groq** (recommended) | `LLM_PROVIDER=groq` | Free tier | ~500 tokens/sec |
| **OpenRouter** | `LLM_PROVIDER=openrouter` | Pay-per-use | Varies by model |

Get keys:
- Groq: https://console.groq.com/keys
- OpenRouter: https://openrouter.ai/keys

## 📝 Track 01 Alignment

- ✅ **Multi-hop reasoning**: Agent follows 1-5 hop paths through CALLS, IMPORTS, INHERITS edges
- ✅ **Graph queries as agent tools**: 7 Cypher-backed tools the agent selects from
- ✅ **Tool selection**: LLM picks the right tool based on the question
- ✅ **Actions based on graph**: Impact analysis drives refactoring suggestions
- ✅ **Explainable results**: Every answer shows the graph path: `A -[CALLS]-> B -[IMPORTS]-> C`

## 📄 License

MIT