const API = window.location.origin;
let simulation, svg, link, node;

async function loadGraph() {
    try {
        const res = await fetch(`${API}/graph?limit=150`);
        const data = await res.json();
        renderGraph(data);
        loadStats();
    } catch (e) {
        document.getElementById('graph-container').innerHTML =
            '<p style="padding:40px;color:#f85149;">Cannot connect to GraphLens API. Start server: python -m src.cli serve</p>';
    }
}

async function loadStats() {
    try {
        const res = await fetch(`${API}/stats`);
        const data = await res.json();
        document.getElementById('stat-nodes').textContent = data.total_nodes;
        document.getElementById('stat-edges').textContent = data.total_edges;
    } catch (e) {}
}

function renderGraph(data) {
    const container = document.getElementById('graph-container');
    container.innerHTML = '';
    const width = container.clientWidth;
    const height = container.clientHeight;
    const typeColors = { 'Module': '#58a6ff', 'Class': '#f78166', 'Function': '#3fb950', 'Method': '#d2a8ff', 'ExternalModule': '#8b949e' };

    svg = d3.select('#graph-container').append('svg').attr('width', width).attr('height', height);
    const g = svg.append('g');
    svg.call(d3.zoom().on('zoom', (event) => { g.attr('transform', event.transform); }));

    simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.edges).id(d => d.id).distance(80))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(20));

    link = g.append('g').selectAll('line').data(data.edges).join('line')
        .attr('class', 'link').attr('stroke-width', 1);

    node = g.append('g').selectAll('g').data(data.nodes).join('g').attr('class', 'node')
        .call(d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended));

    node.append('circle')
        .attr('r', d => d.type === 'Module' ? 10 : d.type === 'Class' ? 8 : 6)
        .attr('fill', d => typeColors[d.type] || '#8b949e');

    node.append('text').attr('dx', 12).attr('dy', 4).text(d => d.label);
    node.append('title').text(d => `${d.label}\nType: ${d.type}\nFile: ${d.file}`);

    simulation.on('tick', () => {
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

function dragstarted(event) { if (!event.active) simulation.alphaTarget(0.3).restart(); event.subject.fx = event.subject.x; event.subject.fy = event.subject.y; }
function dragged(event) { event.subject.fx = event.x; event.subject.fy = event.y; }
function dragended(event) { if (!event.active) simulation.alphaTarget(0); event.subject.fx = null; event.subject.fy = null; }

async function askAgent() {
    const q = document.getElementById('question').value;
    const box = document.getElementById('answer-box');
    box.innerHTML = '<span class="loading">Thinking...</span>';
    try {
        const res = await fetch(`${API}/ask`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question: q}) });
        const data = await res.json();
        box.textContent = data.answer || JSON.stringify(data);
    } catch (e) { box.innerHTML = `<span class="error">Error: ${e.message}</span>`; }
}

async function runImpact() {
    const name = document.getElementById('impact-name').value;
    const dir = document.getElementById('impact-direction').value;
    const el = document.getElementById('impact-result');
    el.innerHTML = '<span class="loading">Analyzing...</span>';
    try {
        const res = await fetch(`${API}/graph/impact?name=${encodeURIComponent(name)}&direction=${dir}`);
        const data = await res.json();
        let html = `<strong>Root:</strong> ${data.root}<br><strong>Affected:</strong> ${data.affected.length} nodes<br>`;
        data.affected.slice(0, 8).forEach(a => { html += `→ ${a.name} (dist: ${a.distance})<br>`; });
        el.innerHTML = html;
    } catch (e) { el.innerHTML = `<span class="error">Error: ${e.message}</span>`; }
}

async function findPath() {
    const source = document.getElementById('path-source').value;
    const target = document.getElementById('path-target').value;
    const el = document.getElementById('path-result');
    el.innerHTML = '<span class="loading">Finding path...</span>';
    try {
        const res = await fetch(`${API}/graph/path?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}`);
        const data = await res.json();
        if (data.ascii) { el.innerHTML = `<code>${data.ascii}</code><br>Hops: ${data.hops}`; }
        else { el.innerHTML = `<span class="error">${data.message || 'No path found'}</span>`; }
    } catch (e) { el.innerHTML = `<span class="error">Error: ${e.message}</span>`; }
}

async function runPageRank() {
    const el = document.getElementById('pagerank-result');
    el.innerHTML = '<span class="loading">Computing...</span>';
    try {
        const res = await fetch(`${API}/graph/pagerank?limit=8`);
        const data = await res.json();
        let html = '';
        data.forEach((n, i) => { html += `${i+1}. <strong>${n.name}</strong> (${n.type}) score: ${n.score}<br>`; });
        el.innerHTML = html;
    } catch (e) { el.innerHTML = `<span class="error">Error: ${e.message}</span>`; }
}

loadGraph();
