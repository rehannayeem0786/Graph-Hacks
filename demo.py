"""
GraphLens Demo Script — for the hackathon submission video.

This script demonstrates the FULL pipeline:
1. Parse a codebase → extract graph
2. Store in FalkorDB
3. Run graph algorithms (PageRank, impact, communities)
4. Ask the AI agent questions with reasoning trace
5. Show explainable graph paths
6. Agent memory — persist and recall across sessions (Track 02)
7. Multi-agent coordination — task queue + handoffs (Track 02)
8. MCP Server — tool selection protocol

Run: python demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(legacy_windows=False)


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

        # Graph Schema
        console.print("\n   📐 [bold]Graph Schema:[/]")
        schema = store.get_schema()
        console.print(f"      {schema}")

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

        # Shortest Path
        console.print("\n   🛤️  [bold]Shortest Path — parse_codebase → GraphStore:[/]")
        path = store.find_shortest_path("parse_codebase", "GraphStore")
        if path:
            nodes = path[0][0]
            edges = path[0][1]
            path_str = f" {nodes[0]} "
            for i, edge in enumerate(edges):
                path_str += f"-[{edge}]-> {nodes[i + 1]} "
            console.print(f"      {path_str}")

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
    """Step 3: AI Agent reasoning over the graph with memory."""
    if store is None:
        console.print(Panel("🤖 Step 3: Agent (skipped — no FalkorDB)", border_style="yellow"))
        return

    console.print(Panel("🤖 Step 3: AI Agent — Multi-hop Reasoning + Memory", border_style="green"))
    from src.agent import GraphLensAgent
    agent = GraphLensAgent(store)

    questions = [
        "What is the most critical module in this codebase?",
        "What would break if I modify the parser?",
    ]

    for q in questions:
        console.print(f"\n   ❓ [yellow]{q}[/]")
        try:
            answer = agent.ask(q)
            console.print(f"   🤖 {answer[:300]}...")

            # Show reasoning trace (Track 01 explainability)
            if agent.last_trace:
                console.print(f"\n   🧠 [bold cyan]Reasoning Trace ({len(agent.last_trace)} steps):[/]")
                for t in agent.last_trace:
                    console.print(f"      [{t['step']}] Tool: [cyan]{t['tool']}[/] → {t['preview'][:80]}...")

            # Show graph path (Track 01 explainability)
            if agent.last_path_nodes:
                console.print(f"   📊 [bold]Graph Path:[/] {' → '.join(agent.last_path_nodes)}")
        except Exception as e:
            console.print(f"   ⚠️  Error: {e}")


def demo_memory(store):
    """Step 4: Agent Memory — Track 02."""
    if store is None:
        console.print(Panel("🧠 Step 4: Memory (skipped — no FalkorDB)", border_style="yellow"))
        return

    console.print(Panel("🧠 Step 4: Agent Memory — Persistent Across Sessions (Track 02)", border_style="red"))
    from src.memory import AgentMemory
    memory = AgentMemory(store, session_id="demo")

    # Store a fact
    memory.remember("config.py is the most critical module — highest PageRank score", "insight")
    memory.remember("Parser changes impact 12+ downstream nodes", "risk")
    console.print("   ✅ Stored 2 facts in FalkorDB graph memory")

    # Recall
    facts = memory.recall(limit=5)
    console.print(f"   📝 Recalled {len(facts)} facts from memory:")
    for f in facts:
        console.print(f"      • {f[0]}")

    # Get agent context
    context = memory.get_context()
    console.print(f"\n   🔄 Agent context for next session:")
    console.print(f"      {context[:200]}")


def demo_multi_agent(store):
    """Step 5: Multi-agent coordination — Track 02."""
    if store is None:
        console.print(Panel("🤝 Step 5: Multi-Agent (skipped — no FalkorDB)", border_style="yellow"))
        return

    console.print(Panel("🤝 Step 5: Multi-Agent Coordination — Shared Graph State (Track 02)", border_style="cyan"))
    from src.multi_agent import AgentBus

    # Register agents
    architect = AgentBus(store)
    architect_id = architect.register("Architect Agent", ["pagerank", "community_detection"])
    console.print(f"   ✅ Registered: Architect Agent ({architect_id})")

    reviewer = AgentBus(store)
    reviewer_id = reviewer.register("Code Reviewer", ["impact_analysis"])
    console.print(f"   ✅ Registered: Code Reviewer ({reviewer_id})")

    # Create and claim tasks
    task_id = architect.create_task("Identify critical modules", priority=9)
    console.print(f"   📋 Created task: {task_id}")

    task = reviewer.claim_task()
    console.print(f"   🎯 Reviewer claimed: {task.get('description', 'N/A')}")

    reviewer.complete_task(task["id"], "config.py is most critical")
    console.print(f"   ✅ Task completed")

    # Handoff
    handoff_id = reviewer.handoff("Architect Agent", "Prioritize config.py refactoring")
    console.print(f"   🤝 Handoff sent: {handoff_id}")

    # Shared state
    state = architect.get_shared_state()
    console.print(f"   📊 Shared State: {state}")


def demo_mcp():
    """Step 6: MCP Server — Tool Selection."""
    console.print(Panel("🔌 Step 6: MCP Server — Tool Selection Protocol", border_style="cyan"))
    from src.mcp_server import TOOLS
    console.print(f"   ✅ {len(TOOLS)} tools exposed via MCP:")
    for tool in TOOLS:
        console.print(f"      • {tool['name']}: {tool['description'][:60]}")


def main():
    console.print(Panel(
        "🔍 [bold]GraphLens[/] — FalkorDB-Powered AI Code Intelligence\n"
        "   Graph Hacks 2026 | Track 01 + Track 02\n"
        "   ─────────────────────────────────────────",
        border_style="bright_blue",
    ))

    parse_result = demo_parser()
    store = demo_graph_store(parse_result)
    demo_agent(store)
    demo_memory(store)
    demo_multi_agent(store)
    demo_mcp()

    console.print(Panel(
        "✅ [bold green]Demo Complete![/]\n\n"
        "GraphLens demonstrates:\n"
        "  [cyan]Track 01:[/]\n"
        "  • Multi-hop reasoning over code graphs\n"
        "  • 7 graph algorithm tools backed by Cypher\n"
        "  • Tool selection via MCP (JSON-RPC)\n"
        "  • Explainable answers with graph path animation\n"
        "  • Reasoning trace (each tool call visible)\n\n"
        "  [magenta]Track 02:[/]\n"
        "  • Persistent agent memory in FalkorDB\n"
        "  • Auto-remember & auto-recall across sessions\n"
        "  • Multi-agent task queue & handoffs\n"
        "  • All coordination through graph state\n\n"
        "  [green]Dashboard:[/] python -m src.cli serve → http://localhost:8000",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
