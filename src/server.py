"""
GraphLens FastAPI Server — REST API + WebSocket for the demo UI.

Endpoints:
  POST /ingest          — parse a codebase into the graph
  POST /ask             — ask the agent a question
  GET  /stats           — graph statistics
  GET  /health          — health check
  GET  /graph           — full graph as D3.js JSON (visualization)
  GET  /graph/path      — shortest path visualization
  GET  /graph/impact    — impact analysis visualization
  GET  /graph/communities — community detection visualization
  GET  /graph/pagerank  — top nodes by importance
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.parser import parse_codebase
from src.graph_store import GraphStore
from src.agent import GraphLensAgent
from src.visualization import (
    get_graph_json, get_path_visualization,
    get_impact_visualization, get_community_visualization,
)

app = FastAPI(title="GraphLens API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    path: str


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "GraphLens"}


@app.post("/ingest")
def ingest(req: IngestRequest):
    result = parse_codebase(req.path)
    store = GraphStore()
    store.clear()
    stats = store.ingest(result)
    return {"nodes_created": stats["nodes_created"], "edges_created": stats["edges_created"]}


@app.post("/ask")
def ask(req: AskRequest):
    store = GraphStore()
    agent = GraphLensAgent(store)
    answer = agent.ask(req.question)
    return {"answer": answer}


@app.get("/stats")
def stats():
    store = GraphStore()
    return store.get_graph_stats()


@app.get("/graph")
def graph_json(limit: int = 200):
    """Full graph as D3.js force-directed graph data."""
    store = GraphStore()
    return get_graph_json(store, limit)


@app.get("/graph/path")
def graph_path(source: str, target: str):
    """Shortest path between two entities."""
    store = GraphStore()
    return get_path_visualization(store, source, target)


@app.get("/graph/impact")
def graph_impact(name: str, direction: str = "downstream"):
    """Impact analysis visualization."""
    store = GraphStore()
    return get_impact_visualization(store, name, direction)


@app.get("/graph/communities")
def graph_communities():
    """Community detection visualization."""
    store = GraphStore()
    return get_community_visualization(store)


@app.get("/graph/pagerank")
def graph_pagerank(limit: int = 10):
    """Top nodes by importance."""
    store = GraphStore()
    results = store.pagerank(limit)
    return [
        {"name": r[0], "type": r[1], "file": r[2], "score": r[5]}
        for r in results
    ]


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Simple dashboard page."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>GraphLens</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 40px; }
        h1 { color: #58a6ff; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin: 10px 0; }
        a { color: #58a6ff; }
        code { background: #21262d; padding: 2px 6px; border-radius: 4px; }
    </style>
    </head>
    <body>
        <h1>🔍 GraphLens — AI Code Intelligence</h1>
        <div class="card">
            <h3>API Endpoints</h3>
            <ul>
                <li><code>POST /ingest</code> — Parse codebase into graph</li>
                <li><code>POST /ask</code> — Ask the AI agent</li>
                <li><code>GET /stats</code> — Graph statistics</li>
                <li><code>GET /graph</code> — D3.js graph data</li>
                <li><code>GET /graph/path?source=X&target=Y</code> — Path visualization</li>
                <li><code>GET /graph/impact?name=X</code> — Impact analysis</li>
                <li><code>GET /graph/communities</code> — Code clusters</li>
                <li><code>GET /graph/pagerank</code> — Most critical nodes</li>
            </ul>
        </div>
        <div class="card">
            <h3>Quick Test</h3>
            <p>Try: <code>curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"What is the most critical module?"}'</code></p>
        </div>
    </body>
    </html>
    """