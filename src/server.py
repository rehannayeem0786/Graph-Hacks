"""
GraphLens FastAPI Server — REST API + WebSocket for the demo UI.

Endpoints:
  POST /ingest     — parse a codebase into the graph
  POST /ask        — ask the agent a question
  GET  /stats      — graph statistics
  GET  /health     — health check
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.parser import parse_codebase
from src.graph_store import GraphStore
from src.agent import GraphLensAgent

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