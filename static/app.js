/* ═══════════════════════════════════════════════════════════
   GraphLens — Premium Frontend Logic
   Graph Hacks 2026 · Powered by FalkorDB
   ═══════════════════════════════════════════════════════════ */

const API = window.location.origin;
let simulation, svg, g, linkGroup, nodeGroup, edgeLabelGroup;
let zoomBehavior, showLabels = true, showEdgeLabels = false;
let allNodes = [], allEdges = [], activeFilter = 'all', currentSearchQuery = '';
const COLORS = {
  Module: '#6366f1', Class: '#f97316', Function: '#10b981',
  Method: '#a78bfa', ExternalModule: '#64748b',
  Agent: '#f59e0b', Memory: '#ec4899', Task: '#14b8a6', Call: '#06b6d4'
};

/* ═══ Initialization ═══ */
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  loadGraph();
  loadStats();
  checkConnection();
  initCmdPalette();
  initKeyboard();
  initTour();
  initParticles();
});

/* ═══ Tab System ═══ */
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(t => {
    t.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(x => x.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      document.getElementById('tab-' + t.dataset.tab).classList.add('active');
    });
  });
}

/* ═══ Keyboard Shortcuts ═══ */
function initKeyboard() {
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); toggleCmdPalette(); }
    if (e.key === 'Escape') { closeCmdPalette(); closeDetail(); }
  });
}

/* ═══ Tour System ═══ */
const TOUR_STEPS = [
  { title: 'Welcome to GraphLens', text: 'Turn any codebase into a queryable knowledge graph. Ask natural language questions and get explainable, graph-backed answers — all powered by FalkorDB.' },
  { title: 'Interactive Code Graph', text: 'Explore your code as a force-directed graph. Drag nodes, zoom, filter by type, and click any node to see its connections and relationships.' },
  { title: 'AI Agent with Graph Reasoning', text: 'Ask questions like "What breaks if I change the parser?" The AI agent reasons over the graph using Cypher queries and shows the exact path it followed.' },
  { title: 'Graph Algorithms as Tools', text: 'Run PageRank, impact analysis, shortest path, community detection, and even raw Cypher queries — all backed by FalkorDB graph traversals.' },
  { title: 'Memory & Multi-Agent', text: 'The agent stores learned facts in FalkorDB memory. Multiple specialized agents coordinate through shared graph state — tasks, handoffs, and decisions all live in the graph.' },
  { title: 'Try It Now!', text: 'Click a suggestion chip, press Ctrl+K to search, or try the Cypher playground. The graph is live and ready to explore. Hit "Run Demo" for a guided walkthrough.' }
];
let tourStep = 0;
function initTour() {
  const dots = document.getElementById('tour-dots');
  dots.innerHTML = TOUR_STEPS.map((_, i) => `<div class="tour-dot${i === 0 ? ' active' : ''}"></div>`).join('');
}
function nextTour() {
  tourStep++;
  if (tourStep >= TOUR_STEPS.length) { closeTour(); return; }
  document.getElementById('tour-title').textContent = TOUR_STEPS[tourStep].title;
  document.getElementById('tour-text').textContent = TOUR_STEPS[tourStep].text;
  document.querySelectorAll('.tour-dot').forEach((d, i) => d.classList.toggle('active', i === tourStep));
  if (tourStep === TOUR_STEPS.length - 1) {
    document.getElementById('tour-next').innerHTML = 'Start Exploring 🎉';
  }
}
function closeTour() { document.getElementById('tour').classList.remove('active'); }

/* ═══ Particles (Hardware-Accelerated) ═══ */
function initParticles() {
  const c = document.getElementById('particles');
  if (!c) return;
  for (let i = 0; i < 6; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.left = (15 + i * 14) + '%';
    p.style.animationDuration = (14 + i * 3) + 's';
    p.style.animationDelay = (i * 2) + 's';
    const size = (1.5 + (i % 2)) + 'px';
    p.style.width = size; p.style.height = size;
    c.appendChild(p);
  }
}

/* ═══ Command Palette ═══ */
function initCmdPalette() {
  const input = document.getElementById('cmd-input');
  input.addEventListener('input', () => searchCmd(input.value));
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const sel = document.querySelector('.cmd-item.selected');
      if (sel) sel.click();
    }
  });
}
function toggleCmdPalette() {
  const el = document.getElementById('cmd-palette');
  el.classList.toggle('open');
  if (el.classList.contains('open')) {
    document.getElementById('cmd-input').value = '';
    document.getElementById('cmd-results').innerHTML = '';
    setTimeout(() => document.getElementById('cmd-input').focus(), 50);
  }
}
function closeCmdPalette() { document.getElementById('cmd-palette').classList.remove('open'); }
const PALETTE_ACTIONS = [
  { label: 'Run Full Live Demo', icon: '▶', category: 'Action', run: () => runDemo() },
  { label: 'Compute PageRank (Critical Code)', icon: '🏆', category: 'Algorithm', run: () => { document.querySelector('[data-tab="analysis"]').click(); runPR(); } },
  { label: 'Analyze Blast Radius / Impact', icon: '💥', category: 'Algorithm', run: () => { document.querySelector('[data-tab="analysis"]').click(); runImpact(); } },
  { label: 'Detect Graph Communities', icon: '🏘️', category: 'Algorithm', run: () => { document.querySelector('[data-tab="explore"]').click(); runComm(); } },
  { label: 'Visualize Live FalkorDB Schema', icon: '📐', category: 'FalkorDB', run: () => { document.querySelector('[data-tab="explore"]').click(); loadSchema(); } },
  { label: 'Find Shortest Path in Graph', icon: '🛤️', category: 'Algorithm', run: () => { document.querySelector('[data-tab="explore"]').click(); findPath(); } },
  { label: 'Inspect Persistent Graph Memory', icon: '🧠', category: 'Memory', run: () => { document.querySelector('[data-tab="memory"]').click(); loadMemories(); } },
  { label: 'Multi-Agent Collective Analysis', icon: '🤝', category: 'Multi-Agent', run: () => { document.querySelector('[data-tab="multi"]').click(); runMultiAgent(); } },
  { label: 'Export Graph as SVG', icon: '💾', category: 'Tools', run: () => exportSVG() },
  { label: 'Reset Camera View', icon: '🎯', category: 'View', run: () => resetView() },
  { label: 'Toggle Node Labels', icon: '🏷️', category: 'View', run: () => toggleLabels() },
  { label: 'Toggle Edge Relationships', icon: '🔗', category: 'View', run: () => toggleEdgeLabels() }
];

async function searchCmd(q) {
  const box = document.getElementById('cmd-results');
  const term = q.toLowerCase().trim();
  if (!term) { box.innerHTML = ''; return; }

  let html = '';
  // 1. Filter matching actions
  const matchingActions = PALETTE_ACTIONS.filter(a => a.label.toLowerCase().includes(term) || a.category.toLowerCase().includes(term));
  if (matchingActions.length > 0) {
    html += '<div style="font-size:.6rem;text-transform:uppercase;color:var(--accent-indigo);padding:6px 12px;font-weight:700">Quick Actions</div>';
    matchingActions.slice(0, 4).forEach((a, idx) => {
      html += `<div class="cmd-item" onclick="PALETTE_ACTIONS.find(x => x.label===\`${a.label}\`).run();closeCmdPalette();">` +
        `<span>${a.icon}</span><span>${escapeHtml(a.label)}</span>` +
        `<span style="margin-left:auto;font-size:.6rem;color:var(--accent-indigo);background:rgba(99,102,241,.1);padding:2px 6px;border-radius:4px">${a.category}</span></div>`;
    });
  }

  // 2. Fetch matching nodes from graph
  try {
    const r = await fetch(API + '/graph/search?q=' + encodeURIComponent(term) + '&limit=6');
    const nodes = await r.json();
    if (nodes && nodes.length > 0) {
      html += '<div style="font-size:.6rem;text-transform:uppercase;color:var(--accent-cyan);padding:6px 12px;font-weight:700">Graph Entities</div>';
      nodes.forEach(n => {
        const color = COLORS[n.type] || '#64748b';
        html += `<div class="cmd-item" onclick="focusNode('${n.name}');closeCmdPalette();">` +
          `<span style="color:${color}">●</span><span>${escapeHtml(n.name)}</span>` +
          `<span style="margin-left:auto;font-size:.6rem;color:var(--text-muted)">${n.type}</span></div>`;
      });
    }
  } catch (e) { /* ignore search error */ }

  box.innerHTML = html || '<div class="cmd-item" style="color:var(--text-muted)">No matching actions or nodes found</div>';
}

/* ═══ Pipeline Step Activation ═══ */
function activatePipelineStep(stepId) {
  ['pip-codebase', 'pip-parser', 'pip-falkordb', 'pip-agent', 'pip-answer'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove('pip-active');
  });
  if (stepId) {
    const el = document.getElementById(stepId);
    if (el) el.classList.add('pip-active');
  }
}

/* ═══ Connection Check ═══ */
async function checkConnection() {
  try {
    const r = await fetch(API + '/db-status');
    const d = await r.json();
    if (d.status === 'connected') {
      const isCloud = d.host && !d.host.includes('localhost') && !d.host.includes('127.0.0.1');
      const label = isCloud ? 'FalkorDB Cloud' : 'FalkorDB';
      document.getElementById('conn-badge').innerHTML = `<span class="dot"></span> Connected · ${label}`;
    } else {
      document.getElementById('conn-badge').innerHTML = '<span class="dot" style="background:#f59e0b"></span> DB Syncing...';
    }
  } catch (e) {
    try {
      const r2 = await fetch(API + '/health');
      await r2.json();
      document.getElementById('conn-badge').innerHTML = '<span class="dot"></span> Connected';
    } catch (e2) {
      document.getElementById('conn-badge').innerHTML = '❌ Offline';
      document.getElementById('conn-badge').classList.remove('badge-live');
    }
  }
}

/* ═══ Stats Loading (4-stat grid) ═══ */
async function loadStats() {
  try {
    const r = await fetch(API + '/stats');
    const d = await r.json();
    animateCounter('s-nodes', d.total_nodes || 0);
    animateCounter('s-edges', d.total_edges || 0);
    const typeCount = d.node_types ? Object.keys(d.node_types).length : 0;
    animateCounter('s-types', typeCount);
    animateCounter('s-time', Math.max(1, Math.round(d.query_time_ms || 1)));
  } catch (e) { /* Graph not loaded yet */ }
}
function animateCounter(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const dur = 900, start = performance.now();
  function tick(now) {
    const p = Math.min((now - start) / dur, 1);
    const ease = 1 - Math.pow(1 - p, 4); // quartic ease-out
    el.textContent = Math.round(target * ease);
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ═══ Suggestion Chips ═══ */
function askSuggestion(chip) {
  document.getElementById('q').value = chip.textContent;
  askAgent();
}

/* ═══ Graph Loading & Rendering (60/120 FPS Optimized) ═══ */
async function loadGraph() {
  try {
    const r = await fetch(API + '/graph?limit=500');
    const d = await r.json();
    allNodes = d.nodes || [];
    allEdges = d.edges || [];
    updateFilterCounts();
    renderGraph(d);
  } catch (e) {
    document.getElementById('graph-container').innerHTML =
      '<div style="display:flex;align-items:center;justify-content:center;height:100%;flex-direction:column;gap:16px;color:var(--text-muted)">' +
      '<span style="font-size:2.5rem">🔌</span>' +
      '<p style="font-size:.9rem;font-weight:600">Cannot connect to GraphLens server</p>' +
      '<code style="font-size:.72rem;background:var(--bg-glass);padding:10px 18px;border-radius:var(--radius-md);border:1px solid var(--border-default)">python -m src.cli serve</code></div>';
  }
}

function updateFilterCounts() {
  const counts = { all: allNodes.length };
  allNodes.forEach(n => {
    counts[n.type] = (counts[n.type] || 0) + 1;
  });
  document.querySelectorAll('.filter-chip').forEach(chip => {
    const type = chip.dataset.type;
    const label = type === 'all' ? 'All' : type === 'ExternalModule' ? 'External' : type;
    const count = counts[type] || (type === 'all' ? allNodes.length : 0);
    chip.textContent = count > 0 ? `${label} (${count})` : label;
  });
}

function renderGraph(data) {
  const c = document.getElementById('graph-container');
  c.innerHTML = '';
  const W = c.clientWidth || 800, H = c.clientHeight || 600;

  svg = d3.select('#graph-container').append('svg').attr('width', W).attr('height', H);

  // Precalculate node degrees for dynamic sizing
  const nodeDegrees = {};
  data.edges.forEach(e => {
    const sid = typeof e.source === 'object' ? e.source.id : e.source;
    const tid = typeof e.target === 'object' ? e.target.id : e.target;
    nodeDegrees[sid] = (nodeDegrees[sid] || 0) + 1;
    nodeDegrees[tid] = (nodeDegrees[tid] || 0) + 1;
  });
  const getNodeR = d => {
    const deg = nodeDegrees[d.id] || 0;
    const base = d.type === 'Module' ? 16 : d.type === 'Class' ? 12 : d.type === 'Function' ? 9 : d.type === 'Method' ? 8 : 7;
    return Math.min(base + Math.min(deg * 0.8, 8), 24);
  };

  const defs = svg.append('defs');

  // Radial gradients for vibrant futuristic 3D sphere look (0% CPU filter overhead)
  Object.entries(COLORS).forEach(([type, hex]) => {
    const rad = defs.append('radialGradient')
      .attr('id', 'grad-' + type)
      .attr('cx', '35%').attr('cy', '35%').attr('r', '65%');
    rad.append('stop').attr('offset', '0%').attr('stop-color', '#ffffff').attr('stop-opacity', '0.55');
    rad.append('stop').attr('offset', '45%').attr('stop-color', hex).attr('stop-opacity', '1');
    rad.append('stop').attr('offset', '100%').attr('stop-color', hex).attr('stop-opacity', '0.8');
  });

  // Arrow marker
  defs.append('marker').attr('id', 'arrowhead').attr('viewBox', '0 -5 10 10')
    .attr('refX', 24).attr('refY', 0).attr('markerWidth', 6).attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path').attr('d', 'M0,-4L10,0L0,4').attr('fill', 'rgba(99,102,241,.35)');

  g = svg.append('g');
  zoomBehavior = d3.zoom().scaleExtent([.1, 8]).on('zoom', e => g.attr('transform', e.transform));
  svg.call(zoomBehavior);

  // Spacious force simulation: strong repulsion, collision boundaries, and type-based link distances
  simulation = d3.forceSimulation(data.nodes)
    .alphaDecay(0.035)
    .velocityDecay(0.38)
    .force('link', d3.forceLink(data.edges).id(d => d.id).distance(d => {
      const sType = typeof d.source === 'object' ? d.source.type : '';
      const tType = typeof d.target === 'object' ? d.target.type : '';
      if (sType === 'Module' || tType === 'Module') return 115;
      if (sType === 'Class' || tType === 'Class') return 95;
      return 80;
    }).strength(0.65))
    .force('charge', d3.forceManyBody().strength(-360).distanceMax(600))
    .force('collide', d3.forceCollide().radius(d => getNodeR(d) + 16).iterations(2))
    .force('center', d3.forceCenter(W / 2, H / 2))
    .force('x', d3.forceX(W / 2).strength(0.016))
    .force('y', d3.forceY(H / 2).strength(0.016));

  // Pre-warm 50 ticks so the graph appears instantly organized and balanced
  for (let i = 0; i < 50; ++i) simulation.tick();

  // Links
  linkGroup = g.append('g').attr('class', 'links');
  const links = linkGroup.selectAll('line').data(data.edges).join('line')
    .attr('class', 'link')
    .attr('stroke-width', 1.2)
    .attr('marker-end', 'url(#arrowhead)');

  // Edge labels
  edgeLabelGroup = g.append('g').attr('class', 'edge-labels');
  edgeLabelGroup.selectAll('text').data(data.edges).join('text')
    .attr('class', 'edge-label' + (showEdgeLabels ? ' visible' : ''))
    .attr('dominant-baseline', 'central')
    .attr('text-anchor', 'middle')
    .text(d => d.type);

  // Position edge labels immediately
  updateEdgeLabelPositions();

  // Nodes
  nodeGroup = g.append('g').attr('class', 'nodes');
  const nodes = nodeGroup.selectAll('g').data(data.nodes).join('g')
    .attr('class', 'node')
    .call(d3.drag().on('start', dragStart).on('drag', dragMove).on('end', dragEnd))
    .on('click', (e, d) => showDetail(d))
    .on('mouseenter', (e, d) => highlightConnected(d))
    .on('mouseleave', () => clearHighlight());

  // Elegant static dashed orbit ring for hub nodes
  nodes.filter(d => (nodeDegrees[d.id] || 0) >= 3 || d.type === 'Module')
    .append('circle')
    .attr('class', 'pulse-halo')
    .attr('r', d => getNodeR(d) + 5);

  // Main node sphere (GPU accelerated radial gradients)
  nodes.append('circle')
    .attr('class', 'main-circle')
    .attr('r', getNodeR)
    .attr('fill', d => COLORS[d.type] ? `url(#grad-${d.type})` : '#64748b');

  nodes.append('text')
    .attr('dx', d => getNodeR(d) + 5).attr('dy', 4)
    .text(d => d.label.length > 20 ? d.label.slice(0, 18) + '..' : d.label)
    .style('opacity', showLabels ? 1 : 0);

  nodes.append('title')
    .text(d => `${d.label}\nType: ${d.type}\nConnections: ${nodeDegrees[d.id] || 0}\nFile: ${d.file || 'N/A'}`);

  // Optimized tick handler: sync positions efficiently
  simulation.on('tick', () => {
    links.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
         .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    if (showEdgeLabels) {
      updateEdgeLabelPositions();
    }
    nodes.attr('transform', d => `translate(${d.x},${d.y})`);
  });

  // Initial gentle center zoom
  setTimeout(() => {
    svg.transition().duration(600).call(zoomBehavior.transform, d3.zoomIdentity.translate(0, 0).scale(.76));
  }, 400);
}

/* ═══ Edge Label Positioning ═══ */
function updateEdgeLabelPositions() {
  if (!edgeLabelGroup) return;
  edgeLabelGroup.selectAll('.edge-label')
    .attr('x', d => {
      const sx = (d.source && typeof d.source.x === 'number') ? d.source.x : 0;
      const tx = (d.target && typeof d.target.x === 'number') ? d.target.x : 0;
      return (sx + tx) / 2;
    })
    .attr('y', d => {
      const sy = (d.source && typeof d.source.y === 'number') ? d.source.y : 0;
      const ty = (d.target && typeof d.target.y === 'number') ? d.target.y : 0;
      return (sy + ty) / 2;
    });
}

/* ═══ Drag Handlers (Smooth Alpha) ═══ */
function dragStart(e) { if (!e.active) simulation.alphaTarget(.15).restart(); e.subject.fx = e.subject.x; e.subject.fy = e.subject.y; }
function dragMove(e) { e.subject.fx = e.x; e.subject.fy = e.y; }
function dragEnd(e) { if (!e.active) simulation.alphaTarget(0); e.subject.fx = null; e.subject.fy = null; }

/* ═══ Zoom Controls ═══ */
function zoomIn() { svg.transition().duration(300).call(zoomBehavior.scaleBy, 1.4); }
function zoomOut() { svg.transition().duration(300).call(zoomBehavior.scaleBy, .7); }
function resetView() { svg.transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity); }
function toggleLabels() {
  showLabels = !showLabels;
  const btn = document.getElementById('btn-toggle-labels');
  if (btn) btn.classList.toggle('active', showLabels);
  if (nodeGroup) nodeGroup.selectAll('text').transition().duration(250).style('opacity', showLabels ? 1 : 0);
}
function toggleEdgeLabels() {
  showEdgeLabels = !showEdgeLabels;
  const btn = document.getElementById('btn-toggle-edge-labels');
  if (btn) btn.classList.toggle('active', showEdgeLabels);
  if (edgeLabelGroup) {
    if (showEdgeLabels) {
      updateEdgeLabelPositions();
    }
    edgeLabelGroup.selectAll('.edge-label').classed('visible', showEdgeLabels);
  }
}

/* ═══ Node Search & Filter (Persistent & File-Aware) ═══ */
function isNodeMatch(d, query) {
  if (!query) return true;
  const q = query.toLowerCase();
  const label = (d.label || '').toLowerCase();
  const type = (d.type || '').toLowerCase();
  const file = (d.file || '').toLowerCase();
  const id = (d.id || '').toLowerCase();
  const name = (d.name || '').toLowerCase();
  return label.includes(q) || type.includes(q) || file.includes(q) || id.includes(q) || name.includes(q);
}

function applyGraphFilters() {
  if (!nodeGroup || !linkGroup) return;
  const q = currentSearchQuery;
  const type = activeFilter;

  nodeGroup.selectAll('.node').each(function(d) {
    const matchesSearch = isNodeMatch(d, q);
    const matchesType = (type === 'all' || d.type === type);
    const isVisible = matchesSearch && matchesType;

    d3.select(this)
      .classed('dimmed', !isVisible)
      .classed('search-matched', !!q && isVisible)
      .classed('type-matched', type !== 'all' && isVisible);
  });

  linkGroup.selectAll('.link').each(function(l) {
    const sNode = typeof l.source === 'object' ? l.source : allNodes.find(n => n.id === l.source);
    const tNode = typeof l.target === 'object' ? l.target : allNodes.find(n => n.id === l.target);
    if (!sNode || !tNode) {
      d3.select(this).style('opacity', 0.08);
      return;
    }
    const sVis = isNodeMatch(sNode, q) && (type === 'all' || sNode.type === type);
    const tVis = isNodeMatch(tNode, q) && (type === 'all' || tNode.type === type);
    d3.select(this).style('opacity', (sVis && tVis) ? 1 : (q || type !== 'all' ? 0.08 : 1));
  });

  if (edgeLabelGroup) {
    edgeLabelGroup.selectAll('.edge-label').style('opacity', q || type !== 'all' ? 0.15 : null);
  }

  // Update clear button visibility
  const clearBtn = document.getElementById('search-clear');
  if (clearBtn) clearBtn.style.display = q ? 'flex' : 'none';
}

function searchNodes(q) {
  currentSearchQuery = (q || '').trim();
  applyGraphFilters();
}

function clearNodeSearch() {
  const input = document.getElementById('node-search');
  if (input) {
    input.value = '';
    input.focus();
  }
  searchNodes('');
}

function filterType(type, chip) {
  activeFilter = type;
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  if (chip) chip.classList.add('active');
  applyGraphFilters();
}

/* ═══ Highlight Connected (Preserves Active Search) ═══ */
function highlightConnected(d) {
  if (!nodeGroup || !linkGroup) return;
  const connected = new Set([d.id]);
  allEdges.forEach(e => {
    const sid = typeof e.source === 'object' ? e.source.id : e.source;
    const tid = typeof e.target === 'object' ? e.target.id : e.target;
    if (sid === d.id) connected.add(tid);
    if (tid === d.id) connected.add(sid);
  });
  nodeGroup.selectAll('.node').classed('dimmed', n => !connected.has(n.id));
  linkGroup.selectAll('.link').classed('highlighted', l => {
    const sid = typeof l.source === 'object' ? l.source.id : l.source;
    const tid = typeof l.target === 'object' ? l.target.id : l.target;
    return sid === d.id || tid === d.id;
  });
  if (showEdgeLabels && edgeLabelGroup) {
    edgeLabelGroup.selectAll('.edge-label').style('opacity', l => {
      const sid = typeof l.source === 'object' ? l.source.id : l.source;
      const tid = typeof l.target === 'object' ? l.target.id : l.target;
      return (sid === d.id || tid === d.id) ? 1 : 0.12;
    });
  }
}

function clearHighlight() {
  if (!nodeGroup || !linkGroup) return;
  linkGroup.selectAll('.link').classed('highlighted', false);
  // Restore current search & filter state instead of blindly clearing dimmed
  applyGraphFilters();
}

/* ═══ Graph Path Animation ═══ */
function animateGraphPath(pathNodes) {
  if (!nodeGroup || !linkGroup || !pathNodes || pathNodes.length < 2) return;

  // Clear previous animations
  nodeGroup.selectAll('.node').classed('path-active', false);
  linkGroup.selectAll('.link').classed('path-active', false);

  // Find node objects
  const pathNodeIds = new Set();
  pathNodes.forEach(name => {
    const found = allNodes.find(n => n.label === name || n.name === name || n.id.includes(name));
    if (found) pathNodeIds.add(found.id);
  });

  // Animate with sequential delay
  let delay = 0;
  pathNodes.forEach((name, i) => {
    setTimeout(() => {
      nodeGroup.selectAll('.node').filter(d => d.label === name || d.id.includes(name))
        .classed('path-active', true);

      // Highlight edge between this node and next
      if (i < pathNodes.length - 1) {
        const nextName = pathNodes[i + 1];
        linkGroup.selectAll('.link').filter(l => {
          const sn = typeof l.source === 'object' ? l.source : allNodes.find(n => n.id === l.source);
          const tn = typeof l.target === 'object' ? l.target : allNodes.find(n => n.id === l.target);
          if (!sn || !tn) return false;
          const sName = sn.label || sn.name || '';
          const tName = tn.label || tn.name || '';
          return (sName.includes(name) && tName.includes(nextName)) ||
                 (tName.includes(name) && sName.includes(nextName));
        }).classed('path-active', true);
      }
    }, delay);
    delay += 400;
  });

  // Clear after 8 seconds
  setTimeout(() => {
    nodeGroup.selectAll('.node').classed('path-active', false);
    linkGroup.selectAll('.link').classed('path-active', false);
  }, delay + 6000);
}

/* ═══ Node Detail Panel ═══ */
function showDetail(d) {
  const panel = document.getElementById('detail-panel');
  document.getElementById('d-name').textContent = d.label;
  const badge = document.getElementById('d-type');
  badge.textContent = d.type;
  badge.style.background = (COLORS[d.type] || '#64748b') + '18';
  badge.style.color = COLORS[d.type] || '#64748b';
  badge.style.border = '1px solid ' + (COLORS[d.type] || '#64748b') + '40';
  document.getElementById('d-meta').textContent = `${d.file || 'unknown'}${d.line ? ':' + d.line : ''}`;

  const conns = [];
  allEdges.forEach(e => {
    const sid = typeof e.source === 'object' ? e.source.id : e.source;
    const tid = typeof e.target === 'object' ? e.target.id : e.target;
    if (sid === d.id) conns.push({ dir: '→', name: getNodeLabel(tid), type: e.type });
    if (tid === d.id) conns.push({ dir: '←', name: getNodeLabel(sid), type: e.type });
  });
  const html = conns.slice(0, 15).map(c =>
    `<div class="conn-row">${c.dir} <strong>${escapeHtml(c.name)}</strong> <span style="color:var(--text-muted)">[${c.type}]</span></div>`
  ).join('');
  document.getElementById('d-conns').innerHTML = html
    ? `<div style="font-weight:700;margin-bottom:6px;font-size:.75rem">Connections (${conns.length})</div>${html}`
    : '<em style="color:var(--text-muted)">No connections found</em>';
  panel.classList.add('visible');
}
function getNodeLabel(id) { const n = allNodes.find(x => x.id === id); return n ? n.label : id; }
function closeDetail() { document.getElementById('detail-panel').classList.remove('visible'); }
function focusNode(name) {
  if (!nodeGroup) return;
  const target = allNodes.find(n => n.label === name || n.id === name || (n.name && n.name === name));
  if (target) {
    const input = document.getElementById('node-search');
    if (input) input.value = target.label;
    searchNodes(target.label);

    const x = target.x || 0, y = target.y || 0;
    svg.transition().duration(600).call(zoomBehavior.transform,
      d3.zoomIdentity.translate(svg.attr('width') / 2 - x * 1.5, svg.attr('height') / 2 - y * 1.5).scale(1.5));
    showDetail(target);
  }
}

/* ═══ Export SVG ═══ */
function exportSVG() {
  const svgEl = document.querySelector('#graph-container svg');
  if (!svgEl) return;
  const clone = svgEl.cloneNode(true);
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  const blob = new Blob([clone.outerHTML], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'graphlens-graph.svg'; a.click();
  URL.revokeObjectURL(url);
  toast('Graph exported as SVG', 'ok');
}

/* ═══════════════════════════════════
   API CALLS — Agent (Streaming-ready)
   ═══════════════════════════════════ */
async function askAgent() {
  const q = document.getElementById('q').value.trim();
  if (!q) return;
  const btn = document.getElementById('btn-ask'), box = document.getElementById('ans');
  btn.disabled = true;
  btn.innerHTML = '<span style="display:inline-block;animation:spin 1s linear infinite">⚙</span> Reasoning over graph...';
  box.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div> <span style="color:var(--text-muted);font-size:.72rem">Agent is reasoning over the FalkorDB graph...</span>';

  // Highlight pipeline: AST Parser -> FalkorDB
  activatePipelineStep('pip-parser');
  const pipeTimer = setTimeout(() => activatePipelineStep('pip-falkordb'), 400);

  try {
    // Try SSE streaming first
    const sseUrl = API + '/ask/stream?question=' + encodeURIComponent(q);
    let streamed = false;

    try {
      const es = new EventSource(sseUrl);
      let fullAnswer = '';
      let traceData = [];
      box.innerHTML = '';

      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => { es.close(); reject(new Error('timeout')); }, 30000);

        es.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'token') {
            activatePipelineStep('pip-agent');
            fullAnswer += data.content;
            box.innerHTML = '<div style="white-space:pre-wrap;line-height:1.7;font-size:.8rem">' +
              formatAnswer(fullAnswer) + '<span class="stream-cursor"></span></div>';
            box.scrollTop = box.scrollHeight;
          } else if (data.type === 'trace') {
            traceData = data.trace;
          } else if (data.type === 'done') {
            clearTimeout(timeout);
            clearTimeout(pipeTimer);
            activatePipelineStep('pip-answer');
            setTimeout(() => activatePipelineStep(null), 5000);
            streamed = true;
            es.close();
            renderAgentResponse(fullAnswer, traceData, data.path_nodes);
            resolve();
          } else if (data.type === 'error') {
            clearTimeout(timeout);
            clearTimeout(pipeTimer);
            es.close();
            reject(new Error(data.message));
          }
        };
        es.onerror = () => { clearTimeout(timeout); clearTimeout(pipeTimer); es.close(); reject(new Error('SSE failed')); };
      });
    } catch (sseErr) {
      // Fallback to regular POST
      if (!streamed) {
        activatePipelineStep('pip-falkordb');
        box.innerHTML = '<div class="skeleton" style="height:14px;margin:4px 0"></div>' +
          '<div class="skeleton" style="height:14px;margin:4px 0;width:80%"></div>' +
          '<div class="skeleton" style="height:14px;margin:4px 0;width:60%"></div>';

        const r = await fetch(API + '/ask', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q })
        });
        const d = await r.json();
        activatePipelineStep('pip-answer');
        setTimeout(() => activatePipelineStep(null), 5000);
        renderAgentResponse(d.answer || JSON.stringify(d, null, 2), d.trace || [], d.path_nodes || []);
      }
    }
    toast('Agent reasoned over the graph', 'ok');
  } catch (e) {
    clearTimeout(pipeTimer);
    activatePipelineStep(null);
    box.innerHTML = '<span style="color:var(--accent-rose)">Error: ' + escapeHtml(e.message) + '</span>';
    toast('Agent error', 'err');
  }
  btn.disabled = false;
  btn.innerHTML = '✨ Ask GraphLens';
}

function renderAgentResponse(answer, trace, pathNodes) {
  const box = document.getElementById('ans');
  let html = '<div style="white-space:pre-wrap;line-height:1.7;font-size:.8rem">' + formatAnswer(answer) + '</div>';

  // Graph path visualization
  if (pathNodes && pathNodes.length > 1) {
    html += '<div class="graph-path-viz">';
    pathNodes.forEach((n, i) => {
      html += `<span class="path-node" style="animation-delay:${i * .15}s">${escapeHtml(n)}</span>`;
      if (i < pathNodes.length - 1) html += '<span class="path-edge">→</span>';
    });
    html += '</div>';
    animateGraphPath(pathNodes);
  }

  // Reasoning trace
  if (trace && trace.length > 0) {
    html += '<div class="trace-container">';
    html += '<div class="trace-header">🧠 Agent Reasoning Trace — ' + trace.length + ' graph tool call' + (trace.length > 1 ? 's' : '') + '</div>';
    trace.forEach((t, i) => {
      html += '<div class="trace-step" style="animation-delay:' + (i * .1) + 's">';
      html += '<span class="step-num">' + t.step + '</span>';
      html += '<span class="step-tool">🔧 ' + escapeHtml(t.tool) + '</span>';
      html += '<span class="step-args">' + escapeHtml(JSON.stringify(t.args || {})) + '</span>';
      html += '</div>';
    });
    html += '</div>';
  }

  box.innerHTML = html;
}

function formatAnswer(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong style="color:var(--accent-cyan)">$1</strong>')
    .replace(/`(.*?)`/g, '<code style="background:rgba(99,102,241,.1);padding:1px 6px;border-radius:4px;font-size:.72rem;color:var(--accent-indigo)">$1</code>')
    .replace(/\n/g, '<br>');
}

/* ═══ Impact Analysis ═══ */
async function runImpact() {
  const name = document.getElementById('imp-name').value;
  const dir = document.getElementById('imp-dir').value;
  const el = document.getElementById('imp-res');
  el.innerHTML = '<div class="skeleton" style="height:14px;margin:4px 0"></div>';
  try {
    const r = await fetch(API + '/graph/impact?name=' + encodeURIComponent(name) + '&direction=' + dir);
    const d = await r.json();
    let html = `<strong style="color:var(--accent-amber)">Root:</strong> ${escapeHtml(d.root)} | <strong style="color:var(--accent-rose)">Affected:</strong> ${d.affected.length} nodes\n\n`;
    d.affected.slice(0, 15).forEach(a => {
      html += `  └ ${escapeHtml(a.name)} <span style="color:var(--text-muted)">(dist:${a.distance}${a.via ? ' via ' + a.via.join(',') : ''})</span>\n`;
    });
    el.innerHTML = html;

    // Animate affected nodes on graph
    const pathNames = [d.root, ...d.affected.slice(0, 5).map(a => a.name)];
    animateGraphPath(pathNames);

    toast('Impact analysis complete', 'ok');
  } catch (e) { el.textContent = 'Error: ' + e.message; }
}

/* ═══ PageRank ═══ */
async function runPR() {
  const el = document.getElementById('pr-res');
  el.innerHTML = '<div class="skeleton" style="height:14px;margin:4px 0"></div>';
  try {
    const r = await fetch(API + '/graph/pagerank?limit=10');
    const d = await r.json();
    let html = '';
    d.forEach((n, i) => {
      const bar = '█'.repeat(Math.max(1, Math.round(n.score / 2)));
      html += `<span style="color:var(--accent-indigo)">${i + 1}.</span> <strong>${escapeHtml(n.name)}</strong> <span style="color:var(--text-muted)">(${n.type})</span> <span style="color:var(--accent-emerald)">${bar}</span> ${n.score}\n`;
    });
    el.innerHTML = html || 'No results';
    toast('PageRank computed', 'ok');
  } catch (e) { el.textContent = 'Error: ' + e.message; }
}

/* ═══ Shortest Path ═══ */
async function findPath() {
  const s = (document.getElementById('p-src').value || '').trim();
  const t = (document.getElementById('p-tgt').value || '').trim();
  const el = document.getElementById('p-res');
  if (!s || !t) {
    el.textContent = 'Please enter both a source and target entity name.';
    toast('Enter source and target', 'err');
    return;
  }
  el.innerHTML = '<div class="skeleton" style="height:14px;margin:4px 0"></div>';
  try {
    const r = await fetch(API + '/graph/path?source=' + encodeURIComponent(s) + '&target=' + encodeURIComponent(t));
    if (!r.ok) {
      const err = await r.json().catch(() => null);
      throw new Error(err?.detail || err?.message || 'Server returned status ' + r.status);
    }
    const d = await r.json();
    if (d.nodes && d.nodes.length) {
      let html = '<div class="graph-path-viz" style="margin:0">';
      d.nodes.forEach((n, i) => {
        html += `<span class="path-node" style="animation-delay:${i * .15}s">${escapeHtml(n)}</span>`;
        if (i < d.edges.length) {
          const back = d.directions && d.directions[i] === 'rev';
          html += back
            ? `<span class="path-edge">←[${escapeHtml(d.edges[i])}]—</span>`
            : `<span class="path-edge">-[${escapeHtml(d.edges[i])}]→</span>`;
        }
      });
      html += '</div>';
      html += `\n<span style="color:var(--text-muted);font-size:.7rem">Hops: ${d.hops}</span>`;
      el.innerHTML = html;
      animateGraphPath(d.nodes);
      toast('Path found!', 'ok');
    } else {
      el.textContent = d.message || 'No path found';
      toast('No path found', 'err');
    }
  } catch (e) { el.textContent = 'Error: ' + e.message; }
}

/* ═══ Community Detection ═══ */
async function runComm() {
  const el = document.getElementById('c-res');
  el.innerHTML = '<div class="skeleton" style="height:14px;margin:4px 0"></div>';
  try {
    const r = await fetch(API + '/graph/communities');
    const d = await r.json();
    let html = '';
    d.slice(0, 10).forEach(c => {
      html += `<span style="color:var(--accent-violet)">●</span> <strong>${escapeHtml(c.file)}</strong> <span style="color:var(--text-muted)">(${c.nodes} nodes, ${c.edges} edges)</span>\n`;
    });
    el.innerHTML = html || 'No communities detected';
    toast('Communities detected', 'ok');
  } catch (e) { el.textContent = 'Error: ' + e.message; }
}

/* ═══ Cypher Playground ═══ */
async function runCypher() {
  const q = document.getElementById('cypher-q').value.trim();
  const el = document.getElementById('cypher-res');
  if (!q) return;
  el.innerHTML = '<div class="skeleton" style="height:14px;margin:4px 0"></div>';
  try {
    const r = await fetch(API + '/graph/cypher', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q })
    });
    const d = await r.json();
    if (d.error) {
      el.innerHTML = '<span style="color:var(--accent-rose)">' + escapeHtml(d.error) + '</span>';
    } else {
      el.innerHTML = '<span style="color:var(--accent-emerald)">' + d.results.length + ' rows returned</span>\n\n' +
        escapeHtml(JSON.stringify(d.results, null, 2));
    }
    toast('Query executed', 'ok');
  } catch (e) { el.textContent = 'Error: ' + e.message; }
}

/* ═══ Search API ═══ */
async function searchApi() {
  const q = document.getElementById('search-q').value;
  const el = document.getElementById('search-res');
  if (!q.trim()) return;
  el.innerHTML = '<div class="skeleton" style="height:14px;margin:4px 0"></div>';
  try {
    const r = await fetch(API + '/graph/search?q=' + encodeURIComponent(q) + '&limit=20');
    const d = await r.json();
    let html = '';
    d.forEach(n => {
      html += `<span style="color:${COLORS[n.type] || '#64748b'}">●</span> ${escapeHtml(n.name)} <span style="color:var(--text-muted)">[${n.type}] ${n.file || ''}</span>\n`;
    });
    el.innerHTML = html || 'No results';
    toast(`Found ${d.length} nodes`, 'ok');
  } catch (e) { el.textContent = 'Error: ' + e.message; }
}

/* ═══ Memory Functions (Track 02) ═══ */
async function loadMemories() {
  const el = document.getElementById('memory-list');
  el.innerHTML = '<div class="skeleton" style="height:40px;margin:4px 0"></div>';
  try {
    const r = await fetch(API + '/memory');
    const d = await r.json();
    if (!d.length) { el.innerHTML = '<p style="color:var(--text-muted);font-size:.75rem;text-align:center;padding:20px">No memories stored yet. Ask the agent a question — it auto-remembers key insights!</p>'; return; }
    el.innerHTML = d.map(m =>
      '<div class="memory-item">' +
      '<div class="fact">' + escapeHtml(m.fact) + '</div>' +
      '<div class="meta"><span class="memory-cat">' + escapeHtml(m.category || 'general') + '</span>' +
      '<span>' + (m.timestamp ? new Date(m.timestamp * 1000).toLocaleString() : '') + '</span></div></div>'
    ).join('');
    toast(`Loaded ${d.length} memories`, 'ok');
  } catch (e) { el.innerHTML = '<p style="color:var(--text-muted);font-size:.75rem">Could not load memories. Make sure the server is running.</p>'; }
}

async function storeFact() {
  const fact = document.getElementById('mem-fact').value.trim();
  const cat = document.getElementById('mem-cat').value;
  if (!fact) return;
  try {
    await fetch(API + '/memory', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fact, category: cat })
    });
    document.getElementById('mem-fact').value = '';
    toast('Fact stored in graph memory', 'ok');
    loadMemories();
  } catch (e) { toast('Failed to store fact', 'err'); }
}

/* ═══ Multi-Agent Functions (Track 02) ═══ */
async function runMultiAgent() {
  const el = document.getElementById('multi-res');
  el.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div> <span style="font-size:.72rem;color:var(--text-muted)">Coordinating agents...</span>';
  try {
    const r = await fetch(API + '/multi-agent/analyze', { method: 'POST' });
    const d = await r.json();
    let html = '<span style="color:var(--accent-emerald);font-weight:700">✓ Multi-agent analysis complete</span>\n\n';
    if (d.agents) {
      d.agents.forEach(a => {
        html += `<span style="color:var(--accent-cyan)">●</span> <strong>${escapeHtml(a.name)}</strong>: ${escapeHtml(a.result || 'Complete')}\n`;
      });
    }
    if (d.summary) html += '\n<strong>Summary:</strong> ' + escapeHtml(d.summary);
    el.innerHTML = html;
    toast('Multi-agent coordination complete', 'ok');
    loadSharedState();
  } catch (e) { el.innerHTML = '<span style="color:var(--accent-rose)">Error: ' + escapeHtml(e.message) + '</span>'; }
}

async function loadSharedState() {
  const el = document.getElementById('agent-list');
  try {
    const r = await fetch(API + '/multi-agent/state');
    const d = await r.json();
    let html = '';
    if (d.active_agents !== undefined) {
      html += `<div class="agent-card"><div class="agent-avatar" style="background:rgba(99,102,241,.15)">📊</div>` +
        `<div class="agent-info"><div class="agent-name">Shared State</div>` +
        `<div class="agent-caps">Active Agents: ${d.active_agents} · Pending Tasks: ${Object.values(d.tasks_by_status || {}).reduce((a, b) => a + b, 0)} · Handoffs: ${d.pending_handoffs}</div></div></div>`;
    }
    if (d.agents) {
      d.agents.forEach(a => {
        html += `<div class="agent-card"><div class="agent-avatar" style="background:rgba(16,185,129,.12)">🤖</div>` +
          `<div class="agent-info"><div class="agent-name">${escapeHtml(a.name)}</div>` +
          `<div class="agent-caps">${escapeHtml(a.capabilities || 'General')}</div></div>` +
          `<span class="agent-status ${a.status === 'active' ? 'status-active' : 'status-idle'}">${a.status}</span></div>`;
      });
    }
    el.innerHTML = html || '<p style="color:var(--text-muted);font-size:.75rem">No agents registered yet. Run a multi-agent analysis to see coordination in action.</p>';
  } catch (e) {
    el.innerHTML = '<p style="color:var(--text-muted);font-size:.75rem">Run multi-agent analysis first.</p>';
  }
}

/* ═══ Toast ═══ */
function toast(msg, type) {
  const c = document.getElementById('toasts'), t = document.createElement('div');
  t.className = 'toast toast-' + (type || 'info');
  const icons = { ok: '✅', err: '❌', info: 'ℹ️' };
  t.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${msg}</span>`;
  c.appendChild(t);
  setTimeout(() => {
    t.style.opacity = '0'; t.style.transform = 'translateX(20px)';
    t.style.transition = 'all .3s';
    setTimeout(() => t.remove(), 300);
  }, 3500);
}

/* ═══ Utility ═══ */
function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Inject spin keyframe
const spinStyle = document.createElement('style');
spinStyle.textContent = '@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}';
document.head.appendChild(spinStyle);

/* ═══ Run Demo ═══ */
async function runDemo() {
  closeTour();
  toast('🎬 Demo 1/4: Computing PageRank...', 'info');
  document.querySelector('[data-tab="analysis"]').click();
  runPR();
  await sleep(2500);

  toast('🔥 Demo 2/4: Impact analysis of parser...', 'info');
  document.getElementById('imp-name').value = 'parser';
  runImpact();
  await sleep(2500);

  toast('🧠 Demo 3/4: AI agent reasoning with trace...', 'info');
  document.querySelector('[data-tab="agent"]').click();
  document.getElementById('q').value = 'What is the most critical module and why?';
  askAgent();
  await sleep(5000);

  toast('📐 Demo 4/5: Loading graph data model...', 'info');
  document.querySelector('[data-tab="explore"]').click();
  loadSchema();
  await sleep(2000);

  toast('🧠 Demo 5/5: Showing agent memory...', 'info');
  document.querySelector('[data-tab="memory"]').click();
  loadMemories();
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

/* ═══ Graph Schema Visualizer ═══ */
async function loadSchema() {
  const el = document.getElementById('schema-viz');
  el.innerHTML = '<div class="skeleton" style="height:14px;margin:4px 0"></div><div class="skeleton" style="height:14px;margin:4px 0;width:80%"></div>';
  try {
    const r = await fetch(API + '/graph/schema');
    const d = await r.json();
    let html = '';

    // Stats bar
    html += '<div class="schema-stats-bar">';
    html += '<div class="schema-stat">📊 <strong>' + d.total_nodes + '</strong> Nodes</div>';
    html += '<div class="schema-stat">🔗 <strong>' + d.total_edges + '</strong> Edges</div>';
    const nodeTypeCount = Object.keys(d.node_types || {}).length;
    const edgeTypeCount = Object.keys(d.edge_types || {}).length;
    html += '<div class="schema-stat">🏷️ <strong>' + nodeTypeCount + '</strong> Labels</div>';
    html += '<div class="schema-stat">⇄ <strong>' + edgeTypeCount + '</strong> Rel Types</div>';
    html += '</div>';

    // Node types
    html += '<div class="schema-section-title">Node Labels</div>';
    for (const [label, count] of Object.entries(d.node_types || {})) {
      const color = COLORS[label] || '#64748b';
      const barW = Math.min(100, Math.max(10, (count / d.total_nodes) * 200));
      html += '<div class="schema-pattern">';
      html += '<span class="schema-node-type" style="background:' + color + '18;color:' + color + ';border:1px solid ' + color + '40">' + escapeHtml(label) + '</span>';
      html += '<div style="flex:1;height:4px;background:rgba(99,102,241,.06);border-radius:2px;overflow:hidden"><div style="width:' + barW + '%;height:100%;background:' + color + ';border-radius:2px"></div></div>';
      html += '<span class="schema-count">' + count + '</span>';
      html += '</div>';
    }

    // Relationship patterns
    if (d.patterns && d.patterns.length > 0) {
      html += '<div class="schema-section-title">Relationship Patterns</div>';
      d.patterns.forEach((p, i) => {
        const fromColor = COLORS[p.from] || '#64748b';
        const toColor = COLORS[p.to] || '#64748b';
        html += '<div class="schema-pattern" style="animation-delay:' + (i * .05) + 's">';
        html += '<span class="schema-node-type" style="background:' + fromColor + '18;color:' + fromColor + ';border:1px solid ' + fromColor + '40">' + escapeHtml(p.from) + '</span>';
        html += '<span class="schema-rel">-[' + escapeHtml(p.rel) + ']-→</span>';
        html += '<span class="schema-node-type" style="background:' + toColor + '18;color:' + toColor + ';border:1px solid ' + toColor + '40">' + escapeHtml(p.to) + '</span>';
        html += '<span class="schema-count">×' + p.count + '</span>';
        html += '</div>';
      });
    }

    el.innerHTML = html;
    toast('Schema loaded from FalkorDB', 'ok');
  } catch (e) {
    el.innerHTML = '<span style="color:var(--text-muted);font-size:.75rem">Could not load schema. Make sure the server and FalkorDB are running.</span>';
  }
}
