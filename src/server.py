"""
GraphLens FastAPI Server - REST API + Interactive Dashboard.

Endpoints:
  GET  /           - Dashboard UI
  GET  /health     - Health check
  POST /ingest     - Parse codebase into graph
  POST /ask        - Ask the AI agent
  GET  /stats      - Graph statistics
  GET  /graph      - Full graph as D3.js JSON
  GET  /graph/search   - Search nodes by name
  GET  /graph/path     - Shortest path
  GET  /graph/impact   - Impact analysis
  GET  /graph/communities - Community detection
  GET  /graph/pagerank - Top nodes by importance
"""
from pathlib import Path
from fastapi import FastAPI, HTTPException
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

app = FastAPI(title="GraphLens API", version="2.0.0",
              description="AI Code Intelligence powered by FalkorDB")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


class IngestRequest(BaseModel):
    path: str


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "GraphLens", "version": "2.0.0"}


@app.post("/ingest")
def ingest(req: IngestRequest):
    try:
        result = parse_codebase(req.path)
        store = GraphStore()
        store.clear()
        stats = store.ingest(result)
        return {"nodes_created": stats["nodes_created"],
                "edges_created": stats["edges_created"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask")
def ask(req: AskRequest):
    try:
        store = GraphStore()
        agent = GraphLensAgent(store)
        answer = agent.ask(req.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def stats():
    try:
        store = GraphStore()
        return store.get_graph_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph")
def graph_json(limit: int = 200):
    store = GraphStore()
    return get_graph_json(store, limit)


@app.get("/graph/search")
def graph_search(q: str, limit: int = 20):
    """Search nodes by name substring."""
    try:
        store = GraphStore()
        results = store.query(
            "MATCH (n) WHERE toLower(n.name) CONTAINS toLower($q) "
            "RETURN n.name AS name, labels(n)[0] AS type, n.file AS file "
            "LIMIT $limit", {"q": q, "limit": limit}
        )
        return [{"name": r[0], "type": r[1], "file": r[2]} for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/path")
def graph_path(source: str, target: str):
    store = GraphStore()
    return get_path_visualization(store, source, target)


@app.get("/graph/impact")
def graph_impact(name: str, direction: str = "downstream"):
    store = GraphStore()
    return get_impact_visualization(store, name, direction)


@app.get("/graph/communities")
def graph_communities():
    store = GraphStore()
    return get_community_visualization(store)


@app.get("/graph/pagerank")
def graph_pagerank(limit: int = 10):
    store = GraphStore()
    results = store.pagerank(limit)
    return [{"name": r[0], "type": r[1], "file": r[2], "score": r[5]}
            for r in results]


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Serve the interactive dashboard."""
    index_path = _static_dir / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return "<h1>GraphLens API</h1><p>Visit /docs for API docs.</p>"
