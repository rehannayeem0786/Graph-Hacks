const API=window.location.origin;
let simulation,svg,g,link,node,zoomB,showLabels=true;
document.addEventListener('DOMContentLoaded',()=>{initTabs();loadGraph();loadStats();checkConn();});
function initTabs(){document.querySelectorAll('.tab').forEach(t=>{t.addEventListener('click',()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab-panel').forEach(x=>x.classList.remove('active'));t.classList.add('active');document.getElementById('tab-'+t.dataset.tab).classList.add('active');});});}
async function checkConn(){try{const r=await fetch(API+'/health');await r.json();document.getElementById('conn-pill').innerHTML='\u2705 Connected';}catch(e){document.getElementById('conn-pill').innerHTML='\u274C Offline';}}
async function loadStats(){try{const r=await fetch(API+'/stats');const d=await r.json();document.getElementById('s-nodes').textContent=d.total_nodes||0;document.getElementById('s-edges').textContent=d.total_edges||0;}catch(e){}}
async function loadGraph(){try{const r=await fetch(API+'/graph?limit=200');const d=await r.json();renderGraph(d);}catch(e){document.getElementById('graph-container').innerHTML='<p style="padding:40px;color:#ef4444">Cannot connect. Run: python -m src.cli serve</p>';}}
function renderGraph(data){const c=document.getElementById('graph-container');c.innerHTML='';const W=c.clientWidth,H=c.clientHeight;
const colors={Module:'#6366f1',Class:'#f97316',Function:'#10b981',Method:'#a78bfa',ExternalModule:'#64748b'};
svg=d3.select('#graph-container').append('svg').attr('width',W).attr('height',H);
g=svg.append('g');zoomB=d3.zoom().scaleExtent([.2,5]).on('zoom',e=>g.attr('transform',e.transform));svg.call(zoomB);
simulation=d3.forceSimulation(data.nodes).force('link',d3.forceLink(data.edges).id(d=>d.id).distance(70)).force('charge',d3.forceManyBody().strength(-180)).force('center',d3.forceCenter(W/2,H/2)).force('collision',d3.forceCollide().radius(18));
link=g.append('g').selectAll('line').data(data.edges).join('line').attr('class','link').attr('stroke-width',1.2);
node=g.append('g').selectAll('g').data(data.nodes).join('g').attr('class','node').call(d3.drag().on('start',ds).on('drag',dd).on('end',de));
node.append('circle').attr('r',d=>d.type==='Module'?11:d.type==='Class'?9:6).attr('fill',d=>colors[d.type]||'#64748b');
node.append('text').attr('dx',14).attr('dy',4).text(d=>d.label).style('opacity',showLabels?1:0);
node.append('title').text(d=>d.label+'\nType: '+d.type+'\nFile: '+d.file);
simulation.on('tick',()=>{link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);node.attr('transform',d=>'translate('+d.x+','+d.y+')');});}
function ds(e){if(!e.active)simulation.alphaTarget(.3).restart();e.subject.fx=e.subject.x;e.subject.fy=e.subject.y;}
function dd(e){e.subject.fx=e.x;e.subject.fy=e.y;}
function de(e){if(!e.active)simulation.alphaTarget(0);e.subject.fx=null;e.subject.fy=null;}
function zoomIn(){svg.transition().duration(300).call(zoomB.scaleBy,1.3);}
function zoomOut(){svg.transition().duration(300).call(zoomB.scaleBy,.7);}
function resetView(){svg.transition().duration(500).call(zoomB.transform,d3.zoomIdentity);}
function toggleLabels(){showLabels=!showLabels;if(node)node.selectAll('text').transition().duration(300).style('opacity',showLabels?1:0);}
function searchNodes(q){if(!node)return;if(!q.trim()){node.selectAll('circle').style('opacity',1);return;}const s=q.toLowerCase();node.selectAll('circle').style('opacity',d=>d.label.toLowerCase().includes(s)?1:.12);}
async function askAgent(){const q=document.getElementById('q').value.trim();if(!q)return;const box=document.getElementById('ans'),btn=document.getElementById('btn-ask');btn.disabled=true;btn.textContent='Thinking...';box.innerHTML='<span style="color:var(--a3)">Reasoning over graph...</span>';
try{const r=await fetch(API+'/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});const d=await r.json();box.textContent=d.answer||JSON.stringify(d,null,2);toast('Agent responded','ok');}catch(e){box.textContent='Error: '+e.message;toast('Query failed','err');}finally{btn.disabled=false;btn.innerHTML='\u2728 Ask GraphLens';}}
async function runImpact(){const n=document.getElementById('imp-name').value,dir=document.getElementById('imp-dir').value,el=document.getElementById('imp-res');el.innerHTML='<span style="color:var(--a3)">Analyzing...</span>';
try{const r=await fetch(API+'/graph/impact?name='+encodeURIComponent(n)+'&direction='+dir);const d=await r.json();let h='Root: '+d.root+' | Affected: '+d.affected.length+' nodes\n';d.affected.slice(0,10).forEach(a=>{h+='  \u2192 '+a.name+' (dist:'+a.distance+')\n';});el.textContent=h;toast('Impact done','ok');}catch(e){el.textContent='Error: '+e.message;}}
async function runPR(){const el=document.getElementById('pr-res');el.innerHTML='<span style="color:var(--a3)">Computing...</span>';
try{const r=await fetch(API+'/graph/pagerank?limit=10');const d=await r.json();let h='';d.forEach((n,i)=>{h+=(i+1)+'. '+n.name+' ('+n.type+') '+n.score+'\n';});el.textContent=h;toast('PageRank done','ok');}catch(e){el.textContent='Error: '+e.message;}}
async function findPath(){const s=document.getElementById('p-src').value,t=document.getElementById('p-tgt').value,el=document.getElementById('p-res');el.innerHTML='<span style="color:var(--a3)">Finding...</span>';
try{const r=await fetch(API+'/graph/path?source='+encodeURIComponent(s)+'&target='+encodeURIComponent(t));const d=await r.json();if(d.ascii){el.textContent=d.ascii+'\nHops: '+d.hops;toast('Path found','ok');}else{el.textContent=d.message||'No path';toast('No path','info');}}catch(e){el.textContent='Error: '+e.message;}}
async function runComm(){const el=document.getElementById('c-res');el.innerHTML='<span style="color:var(--a3)">Detecting...</span>';
try{const r=await fetch(API+'/graph/communities');const d=await r.json();let h='';d.slice(0,8).forEach((c,i)=>{h+='Community '+(i+1)+': '+c.file+' ('+c.nodes+' nodes)\n';});el.textContent=h||'No communities';toast('Done','ok');}catch(e){el.textContent='Error: '+e.message;}}
function toast(msg,type){const c=document.getElementById('toasts'),t=document.createElement('div');t.className='toast toast-'+(type||'info');const icons={ok:'\u2705',err:'\u274C',info:'\u2139\uFE0F'};t.innerHTML='<span>'+(icons[type]||'\u2139\uFE0F')+'</span><span>'+msg+'</span>';c.appendChild(t);setTimeout(()=>{t.style.opacity='0';t.style.transform='translateX(20px)';t.style.transition='all .3s';setTimeout(()=>t.remove(),300);},3500);}
