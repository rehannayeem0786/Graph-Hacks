const API=window.location.origin;
let simulation,svg,g,link,node,zoomB,showLabels=true,allNodes=[],allEdges=[],activeFilter='all';
const COLORS={Module:'#6366f1',Class:'#f97316',Function:'#10b981',Method:'#a78bfa',ExternalModule:'#64748b',Agent:'#f59e0b',Memory:'#ec4899',Task:'#14b8a6'};
document.addEventListener('DOMContentLoaded',()=>{initTabs();loadGraph();loadStats();checkConn();initCmdPalette();initKeyboard();});
function initTabs(){document.querySelectorAll('.tab').forEach(t=>{t.addEventListener('click',()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab-panel').forEach(x=>x.classList.remove('active'));t.classList.add('active');document.getElementById('tab-'+t.dataset.tab).classList.add('active');});});}
function initKeyboard(){document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();toggleCmdPalette();}if(e.key==='Escape'){closeCmdPalette();closeDetail();}});}
function initCmdPalette(){const input=document.getElementById('cmd-input');input.addEventListener('input',()=>searchCmd(input.value));input.addEventListener('keydown',e=>{if(e.key==='Enter'){const sel=document.querySelector('.cmd-item.selected');if(sel)sel.click();}});}
function toggleCmdPalette(){const el=document.getElementById('cmd-palette');el.classList.toggle('open');if(el.classList.contains('open')){document.getElementById('cmd-input').value='';document.getElementById('cmd-results').innerHTML='';setTimeout(()=>document.getElementById('cmd-input').focus(),50);}}
function closeCmdPalette(){document.getElementById('cmd-palette').classList.remove('open');}
async function searchCmd(q){const box=document.getElementById('cmd-results');if(!q.trim()){box.innerHTML='';return;}
try{const r=await fetch(API+'/graph/search?q='+encodeURIComponent(q)+'&limit=8');const data=await r.json();
box.innerHTML=data.map(n=>`<div class="cmd-item" onclick="focusNode('${n.name}');closeCmdPalette();"><span class="cmd-icon">\u{1F4CD}</span><span>${n.name}</span><span style="margin-left:auto;font-size:.6rem;color:var(--txt3)">${n.type}</span></div>`).join('')||'<div class="cmd-item">No results</div>';
}catch(e){box.innerHTML='<div class="cmd-item">Error searching</div>';}}
async function checkConn(){try{const r=await fetch(API+'/health');await r.json();document.getElementById('conn-pill').innerHTML='\u2705 Connected';}catch(e){document.getElementById('conn-pill').innerHTML='\u274C Offline';}}
async function loadStats(){try{const r=await fetch(API+'/stats');const d=await r.json();animateCounter('s-nodes',d.total_nodes||0);animateCounter('s-edges',d.total_edges||0);}catch(e){}}
function animateCounter(id,target){const el=document.getElementById(id);const dur=800;const start=performance.now();
function tick(now){const p=Math.min((now-start)/dur,1);const ease=1-Math.pow(1-p,3);el.textContent=Math.round(target*ease);if(p<1)requestAnimationFrame(tick);}requestAnimationFrame(tick);}

async function loadGraph(){try{const r=await fetch(API+'/graph?limit=250');const d=await r.json();allNodes=d.nodes;allEdges=d.edges;renderGraph(d);}catch(e){document.getElementById('graph-container').innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:100%;flex-direction:column;gap:12px;color:var(--txt3)"><span style="font-size:2rem">\u{1F6AB}</span><p>Cannot connect to FalkorDB</p><code style="font-size:.7rem;background:var(--card);padding:8px 14px;border-radius:8px">python -m src.cli serve</code></div>';}}
function renderGraph(data){const c=document.getElementById('graph-container');c.innerHTML='';
const W=c.clientWidth||800,H=c.clientHeight||600;
svg=d3.select('#graph-container').append('svg').attr('width',W).attr('height',H);
const defs=svg.append('defs');
const glow=defs.append('filter').attr('id','glow');
glow.append('feGaussianBlur').attr('stdDeviation','3').attr('result','coloredBlur');
const merge=glow.append('feMerge');merge.append('feMergeNode').attr('in','coloredBlur');merge.append('feMergeNode').attr('in','SourceGraphic');
g=svg.append('g');
zoomB=d3.zoom().scaleExtent([.15,6]).on('zoom',e=>g.attr('transform',e.transform));svg.call(zoomB);
simulation=d3.forceSimulation(data.nodes)
 .force('link',d3.forceLink(data.edges).id(d=>d.id).distance(65))
 .force('charge',d3.forceManyBody().strength(-200))
 .force('center',d3.forceCenter(W/2,H/2))
 .force('collision',d3.forceCollide().radius(d=>d.type==='Module'?20:d.type==='Class'?16:10))
 .force('x',d3.forceX(W/2).strength(.03))
 .force('y',d3.forceY(H/2).strength(.03));
link=g.append('g').selectAll('line').data(data.edges).join('line').attr('class','link').attr('stroke-width',1);
node=g.append('g').selectAll('g').data(data.nodes).join('g').attr('class','node')
 .call(d3.drag().on('start',dragStart).on('drag',dragMove).on('end',dragEnd))
 .on('click',(e,d)=>showDetail(d))
 .on('mouseenter',(e,d)=>highlightConnected(d))
 .on('mouseleave',()=>clearHighlight());
node.append('circle')
 .attr('r',d=>d.type==='Module'?12:d.type==='Class'?9:6)
 .attr('fill',d=>COLORS[d.type]||'#64748b')
 .attr('filter','url(#glow)');
node.append('text').attr('dx',16).attr('dy',4).text(d=>d.label.length>18?d.label.slice(0,16)+'..':d.label).style('opacity',showLabels?1:0);
node.append('title').text(d=>`${d.label}\nType: ${d.type}\nFile: ${d.file}`);
simulation.on('tick',()=>{
 link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
 node.attr('transform',d=>`translate(${d.x},${d.y})`);});
setTimeout(()=>{svg.transition().duration(600).call(zoomB.transform,d3.zoomIdentity.translate(0,0).scale(.85));},800);
}

/* === Drag handlers === */
function dragStart(e){if(!e.active)simulation.alphaTarget(.3).restart();e.subject.fx=e.subject.x;e.subject.fy=e.subject.y;}
function dragMove(e){e.subject.fx=e.x;e.subject.fy=e.y;}
function dragEnd(e){if(!e.active)simulation.alphaTarget(0);e.subject.fx=null;e.subject.fy=null;}

/* === Zoom & Controls === */
function zoomIn(){svg.transition().duration(300).call(zoomB.scaleBy,1.4);}
function zoomOut(){svg.transition().duration(300).call(zoomB.scaleBy,.7);}
function resetView(){svg.transition().duration(500).call(zoomB.transform,d3.zoomIdentity);}
function toggleLabels(){showLabels=!showLabels;if(node)node.selectAll('text').transition().duration(300).style('opacity',showLabels?1:0);}

/* === Node Search / Filter === */
function searchNodes(q){if(!node)return;const s=q.toLowerCase().trim();
node.classed('dimmed',d=>s&&!d.label.toLowerCase().includes(s)&&!d.type.toLowerCase().includes(s));
link.style('opacity',s?.2:1);}

function filterType(type,chip){activeFilter=type;
document.querySelectorAll('.filter-chip').forEach(c=>c.classList.remove('active'));chip.classList.add('active');
if(!node)return;
if(type==='all'){node.classed('dimmed',false);link.style('opacity',1);return;}
node.classed('dimmed',d=>d.type!==type);
link.style('opacity',l=>(l.source.type===type||l.target.type===type)?1:.1);}

/* === Highlight Connected === */
function highlightConnected(d){if(!node||!link)return;
const connected=new Set([d.id]);
allEdges.forEach(e=>{const sid=typeof e.source==='object'?e.source.id:e.source;const tid=typeof e.target==='object'?e.target.id:e.target;
if(sid===d.id)connected.add(tid);if(tid===d.id)connected.add(sid);});
node.classed('dimmed',n=>!connected.has(n.id));
link.classed('highlighted',l=>{const sid=typeof l.source==='object'?l.source.id:l.source;const tid=typeof l.target==='object'?l.target.id:l.target;return sid===d.id||tid===d.id;});}
function clearHighlight(){if(!node)return;node.classed('dimmed',false);link.classed('highlighted',false);}

/* === Node Detail Panel === */
function showDetail(d){const panel=document.getElementById('detail-panel');
document.getElementById('d-name').textContent=d.label;
const badge=document.getElementById('d-type');badge.textContent=d.type;
badge.style.background=(COLORS[d.type]||'#64748b')+'22';badge.style.color=COLORS[d.type]||'#64748b';
document.getElementById('d-meta').textContent=`${d.file||'unknown'}${d.line?':'+d.line:''}`;
/* Find connections */
const conns=[];
allEdges.forEach(e=>{const sid=typeof e.source==='object'?e.source.id:e.source;const tid=typeof e.target==='object'?e.target.id:e.target;
if(sid===d.id)conns.push({dir:'\u2192',name:getNodeLabel(tid),type:e.type});
if(tid===d.id)conns.push({dir:'\u2190',name:getNodeLabel(sid),type:e.type});});
const connHtml=conns.slice(0,12).map(c=>`<div class="conn-item">${c.dir} <strong>${c.name}</strong> <span style="color:var(--txt3)">[${c.type}]</span></div>`).join('');
document.getElementById('d-conns').innerHTML=connHtml?`<div style="font-weight:600;margin-bottom:4px;color:var(--txt)">Connections (${conns.length})</div>${connHtml}`:'<em>No connections found</em>';
panel.classList.add('visible');}
function getNodeLabel(id){const n=allNodes.find(x=>x.id===id);return n?n.label:id;}
function closeDetail(){document.getElementById('detail-panel').classList.remove('visible');}
function focusNode(name){if(!node)return;const target=allNodes.find(n=>n.label===name||n.id===name);
if(target){node.classed('dimmed',n=>n.id!==target.id);setTimeout(()=>clearHighlight(),2000);
/* Pan to node */
const t=d3.zoomTransform(svg.node());const x=target.x||0,y=target.y||0;
svg.transition().duration(600).call(zoomB.transform,d3.zoomIdentity.translate(svg.attr('width')/2-x*1.5,svg.attr('height')/2-y*1.5).scale(1.5));
showDetail(target);}}

/* === Export SVG === */
function exportSVG(){const svgEl=document.querySelector('#graph-container svg');if(!svgEl)return;
const clone=svgEl.cloneNode(true);clone.setAttribute('xmlns','http://www.w3.org/2000/svg');
const blob=new Blob([clone.outerHTML],{type:'image/svg+xml'});
const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='graphlens-graph.svg';a.click();URL.revokeObjectURL(url);
toast('Graph exported as SVG','ok');}

/* === API Calls === */
async function askAgent(){const q=document.getElementById('q').value.trim();if(!q)return;
const box=document.getElementById('ans'),btn=document.getElementById('btn-ask');
btn.disabled=true;btn.innerHTML='<span style="display:inline-block;animation:spin 1s linear infinite">\u2699</span> Reasoning...';
box.innerHTML='<div class="skeleton" style="height:14px;margin:4px 0"></div><div class="skeleton" style="height:14px;margin:4px 0;width:80%"></div><div class="skeleton" style="height:14px;margin:4px 0;width:60%"></div>';
try{const r=await fetch(API+'/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
const d=await r.json();const answer=d.answer||JSON.stringify(d,null,2);
box.innerHTML=formatAnswer(answer);toast('Agent responded','ok');
}catch(e){box.textContent='Error: '+e.message;toast('Query failed','err');}
finally{btn.disabled=false;btn.innerHTML='\u2728 Ask GraphLens';}}

function formatAnswer(text){/* Simple markdown-like formatting */
return text
 .replace(/\*\*(.*?)\*\*/g,'<strong style="color:var(--a3)">$1</strong>')
 .replace(/`(.*?)`/g,'<code style="background:rgba(99,102,241,.1);padding:1px 5px;border-radius:4px;font-size:.7rem">$1</code>')
 .replace(/\n/g,'<br>');}

async function runImpact(){const n=document.getElementById('imp-name').value,dir=document.getElementById('imp-dir').value,el=document.getElementById('imp-res');
el.innerHTML='<div class="skeleton" style="height:14px;margin:4px 0"></div>';
try{const r=await fetch(API+'/graph/impact?name='+encodeURIComponent(n)+'&direction='+dir);const d=await r.json();
let h=`<strong style="color:var(--a5)">Root:</strong> ${d.root} | <strong style="color:var(--danger)">Affected:</strong> ${d.affected.length} nodes\n\n`;
d.affected.slice(0,12).forEach((a,i)=>{h+=`  ${'\u2514'} ${a.name} <span style="color:var(--txt3)">(dist:${a.distance}${a.via?' via '+a.via.join(','):''})</span>\n`;});
el.innerHTML=h;toast('Impact analysis complete','ok');}catch(e){el.textContent='Error: '+e.message;}}

async function runPR(){const el=document.getElementById('pr-res');
el.innerHTML='<div class="skeleton" style="height:14px;margin:4px 0"></div>';
try{const r=await fetch(API+'/graph/pagerank?limit=10');const d=await r.json();
let h='';d.forEach((n,i)=>{const bar='\u2588'.repeat(Math.max(1,Math.round(n.score/2)));
h+=`<span style="color:var(--a1)">${i+1}.</span> <strong>${n.name}</strong> <span style="color:var(--txt3)">(${n.type})</span> <span style="color:var(--a4)">${bar}</span> ${n.score}\n`;});
el.innerHTML=h||'No results';toast('PageRank computed','ok');}catch(e){el.textContent='Error: '+e.message;}}

async function findPath(){const s=document.getElementById('p-src').value,t=document.getElementById('p-tgt').value,el=document.getElementById('p-res');
el.innerHTML='<div class="skeleton" style="height:14px;margin:4px 0"></div>';
try{const r=await fetch(API+'/graph/path?source='+encodeURIComponent(s)+'&target='+encodeURIComponent(t));const d=await r.json();
if(d.ascii){el.innerHTML=`<span style="color:var(--a4)">${d.ascii}</span>\n\n<span style="color:var(--txt3)">Hops: ${d.hops}</span>`;toast('Path found!','ok');}
else{el.textContent=d.message||'No path found';toast('No path found','info');}}catch(e){el.textContent='Error: '+e.message;}}

async function runComm(){const el=document.getElementById('c-res');
el.innerHTML='<div class="skeleton" style="height:14px;margin:4px 0"></div>';
try{const r=await fetch(API+'/graph/communities');const d=await r.json();
let h='';d.slice(0,8).forEach((c,i)=>{h+=`<span style="color:var(--a2)">\u25CF</span> <strong>${c.file}</strong> <span style="color:var(--txt3)">(${c.nodes} nodes, ${c.edges} edges)</span>\n`;});
el.innerHTML=h||'No communities detected';toast('Communities detected','ok');}catch(e){el.textContent='Error: '+e.message;}}

async function searchApi(){const q=document.getElementById('search-q').value,el=document.getElementById('search-res');
if(!q.trim())return;el.innerHTML='<div class="skeleton" style="height:14px;margin:4px 0"></div>';
try{const r=await fetch(API+'/graph/search?q='+encodeURIComponent(q)+'&limit=15');const d=await r.json();
let h='';d.forEach(n=>{h+=`<span style="color:${COLORS[n.type]||'#64748b'}">\u25CF</span> ${n.name} <span style="color:var(--txt3)">[${n.type}] ${n.file||''}</span>\n`;});
el.innerHTML=h||'No results';toast(`Found ${d.length} nodes`,'ok');}catch(e){el.textContent='Error: '+e.message;}}

/* === Toast === */
function toast(msg,type){const c=document.getElementById('toasts'),t=document.createElement('div');
t.className='toast toast-'+(type||'info');
const icons={ok:'\u2705',err:'\u274C',info:'\u2139\uFE0F'};
t.innerHTML=`<span>${icons[type]||'\u2139\uFE0F'}</span><span>${msg}</span>`;
c.appendChild(t);
setTimeout(()=>{t.style.opacity='0';t.style.transform='translateX(20px)';t.style.transition='all .3s';setTimeout(()=>t.remove(),300);},3500);}

/* === Spinner keyframe (injected) === */
const style=document.createElement('style');style.textContent='@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}';document.head.appendChild(style);
