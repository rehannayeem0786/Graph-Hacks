"""
GraphLens CLI — the main entry point for the hackathon demo.

Usage:
  python -m src.cli ingest <path>     Parse a codebase into FalkorDB
  python -m src.cli ask "question"    Ask the agent a question
  python -m src.cli stats             Show graph statistics
  python -m src.cli serve             Start the FastAPI server
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.config import FALKORDB_GRAPH_NAME
from src.parser import parse_codebase
from src.graph_store import GraphStore
from src.agent import GraphLensAgent

console = Console()


def cmd_ingest(path: str):
    """Parse a codebase and store it in FalkorDB."""
    console.print(Panel(f"🔍 Parsing codebase: [bold cyan]{path}[/]", border_style="blue"))
    result = parse_codebase(path)
    console.print(f"  Found [green]{len(result.nodes)}[/] nodes, [green]{len(result.edges)}[/] edges")

    store = GraphStore()
    store.clear()
    stats = store.ingest(result)
    console.print(Panel(
        f"✅ Ingested into FalkorDB graph '{FALKORDB_GRAPH_NAME}'\n"
        f"   Nodes: {stats['nodes_created']}, Edges: {stats['edges_created']}",
        border_style="green",
    ))


def cmd_ask(question: str):
    """Ask the agent a question about the codebase."""
    store = GraphStore()
    agent = GraphLensAgent(store)
    console.print(Panel(f"❓ {question}", border_style="yellow"))
    answer = agent.ask(question)
    console.print(Panel(Markdown(answer), title="🤖 GraphLens", border_style="cyan"))


def cmd_stats():
    """Show graph statistics."""
    store = GraphStore()
    stats = store.get_graph_stats()
    console.print(Panel(
        f"📊 Graph: [bold]{FALKORDB_GRAPH_NAME}[/]\n"
        f"   Total Nodes: {stats['total_nodes']}\n"
        f"   Total Edges: {stats['total_edges']}\n"
        f"   Node Types: {stats['node_types']}\n"
        f"   Edge Types: {stats['edge_types']}",
        border_style="magenta",
    ))


def cmd_serve():
    """Start the FastAPI server."""
    import uvicorn
    from src.server import app
    console.print(Panel("🚀 Starting GraphLens API server on http://localhost:8000", border_style="green"))
    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    if len(sys.argv) < 2:
        console.print("[bold red]Usage:[/] python -m src.cli <ingest|ask|stats|serve> [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "ingest":
        path = sys.argv[2] if len(sys.argv) > 2 else "."
        cmd_ingest(path)
    elif cmd == "ask":
        question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "What is the most important module?"
        cmd_ask(question)
    elif cmd == "stats":
        cmd_stats()
    elif cmd == "serve":
        cmd_serve()
    else:
        console.print(f"[red]Unknown command: {cmd}[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()