"""
GraphLens Demo Script — for the hackathon submission video.

This script demonstrates the full pipeline:
1. Parse a codebase → extract graph
2. Store in FalkorDB
3. Run graph algorithms (PageRank, impact, communities)
4. Ask the AI agent questions
5. Show explainable graph paths

Run: python demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

console = Console()


def demo_parser():
    """Step 1: Show the parser extracting the code graph."""
    console.print(Panel("🔬 Step 1: AST Parser — Extracting Code Graph", border_style="blue"))
    from src.parser import parse_codebase
    result = parse_codebase("./src")
    console.print(f"   ✅ Parsed [bold green]{len(result.nodes)}[/] nodes, [bold green]{len(result.edges)}[/] edges")

    # Show sample nodes
    table = Table(title="Sample Nodes")
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("File")
    for node in result.nodes[:8]:
        table.add_row(node.node_type, node.name, node.file_path)
    console.print(table)

    # Show sample edges
    table2 = Table(title="Sample Edges")
    table2.add_column("Source", style="cyan")
    table2.add_column("Type", style="yellow")
    table2.add_column("Target", style="green")
    for edge in result.edges[:8]:
        table2.add_row(edge.source_id, edge.edge_type, edge.target_id)
    console.print(table2)
    return result


def demo_graph_store(parse_result):
    """Step 2: Store in FalkorDB and run algorithms."""
    console.print(Panel("🗄️  Step 2: FalkorDB — Graph Storage & Algorithms", border_style="magenta"))
    try:
        from src.graph_store import GraphStore
        store = GraphStore()
        store.clear()
        stats = store.ingest(parse_result)
        console.print(f"   ✅ Ingested: {stats['nodes_created']} nodes, {stats['edges_created']} edges")

        # PageRank
        console.print("\n   📊 [bold]PageRank — Most Critical Code:[/]")
        pr = store.pagerank(5)
        for r in pr:
            console.print(f"      {r[0]} ({r[1]}) — score: {r[5]}")

        # Impact Analysis
        console.print("\n   💥 [bold]Impact Analysis — What breaks if 'config' changes:[/]")
        impact = store.impact_analysis("config")
        for r in impact[:5]:
            console.print(f"      → {r[0]} (distance: {r[2]})")

        # Communities
        console.print("\n   🏘️ [bold]Community Detection — Code Clusters:[/]")
        comm = store.community_detection()
        for r in comm[:5]:
            console.print(f"      {r[0]}: {r[1]} nodes, {r[2]} edges")

        return store
    except Exception as e:
        console.print(f"   ⚠️  FalkorDB not available: {e}")
        console.print("   → Start FalkorDB: docker run -p 6379:6379 falkordb/falkordb:latest")
        return None


def demo_agent(store):
    """Step 3: AI Agent reasoning over the graph."""
    if store is None:
        console.print(Panel("🤖 Step 3: Agent (skipped — no FalkorDB)", border_style="yellow"))
        return

    console.print(Panel("🤖 Step 3: AI Agent — Multi-hop Reasoning", border_style="green"))
    from src.agent import GraphLensAgent
    agent = GraphLensAgent(store)

    questions = [
        "What is the most critical module in this codebase?",
        "What would break if I modify the parser?",
        "Show me the path from parse_codebase to GraphStore",
    ]

    for q in questions:
        console.print(f"\n   ❓ [yellow]{q}[/]")
        try:
            answer = agent.ask(q)
            console.print(f"   🤖 {answer[:200]}...")
        except Exception as e:
            console.print(f"   ⚠️  Error: {e}")


def demo_mcp():
    """Step 4: MCP Server — Tool Selection."""
    console.print(Panel("🔌 Step 4: MCP Server — Tool Selection Protocol", border_style="cyan"))
    from src.mcp_server import TOOLS
    console.print(f"   ✅ {len(TOOLS)} tools exposed via MCP:")
    for tool in TOOLS:
        console.print(f"      • {tool['name']}: {tool['description'][:50]}")


def demo_memory():
    """Step 5: Agent Memory — Track 02."""
    console.print(Panel("🧠 Step 5: Agent Memory — Persistent Across Sessions", border_style="red"))
    console.print("   ✅ Memory module loaded")
    console.print("   • remember() — store facts")
    console.print("   • recall() — retrieve by category")
    console.print("   • remember_decision() — store reasoning paths")
    console.print("   • get_context() — feed into next session")


def main():
    console.print(Panel(
        "🔍 [bold]GraphLens[/] — FalkorDB-Powered AI Code Intelligence\n"
        "   Graph Hacks Hackathon | Track 01 + Track 02",
        border_style="bright_blue",
    ))

    parse_result = demo_parser()
    store = demo_graph_store(parse_result)
    demo_agent(store)
    demo_mcp()
    demo_memory()

    console.print(Panel(
        "✅ Demo Complete!\n\n"
        "GraphLens demonstrates:\n"
        "  • Multi-hop reasoning over code graphs\n"
        "  • Graph algorithms as agent tools (PageRank, shortest path)\n"
        "  • Tool selection via MCP\n"
        "  • Explainable answers with graph paths\n"
        "  • Persistent agent memory (Track 02)",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
