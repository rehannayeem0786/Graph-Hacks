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

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
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

# Serve static files (D3.js visualization UI)
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


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
    """Serve the D3.js visualization dashboard."""
    index_path = _static_dir / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return "<h1>GraphLens API</h1><p>Visit /docs for API documentation.</p>"