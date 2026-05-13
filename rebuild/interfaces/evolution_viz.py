"""
rebuild.evolution_viz — D3.js Code Evolution playback visualization.

Generates HTML with D3.js force-directed graph showing dependency evolution over time.
"""

from __future__ import annotations
import json
from pathlib import Path


def generate_evolution_html(
    timeline_path: Path, output_path: Path, title: str = "Code Evolution"
) -> Path:
    """Generate HTML file with D3.js evolution playback visualization."""
    # Load timeline data
    with open(timeline_path) as f:
        timeline_data = json.load(f)

    snapshots = timeline_data.get("snapshots", [])
    repo_path = timeline_data.get("repo_path", "")

    html = _render_html(snapshots, repo_path, title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def _render_html(snapshots: list, repo_path: str, title: str) -> str:
    """Render the HTML with D3.js visualization."""
    snapshots_js = json.dumps(snapshots)

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  :root {{
    --bg: #0f172a;
    --card-bg: rgba(30, 41, 59, 0.7);
    --border: rgba(255, 255, 255, 0.1);
    --text: #f8fafc;
    --text-dim: #94a3b8;
    --primary: #6366f1;
    --success: #10b981;
  }}
  body {{
    font-family: 'Outfit', sans-serif;
    margin: 0;
    background: var(--bg);
    background-image: radial-gradient(circle at 0% 100%, rgba(99, 102, 241, 0.1) 0%, transparent 50%);
    color: var(--text);
    min-height: 100vh;
  }}
  nav {{
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(12px);
    padding: 16px 32px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid var(--border);
  }}
  .brand {{ font-weight: 800; font-size: 1.4rem; letter-spacing: -0.02em; }}

  .content {{ padding: 32px; max-width: 1400px; margin: 0 auto; }}
  h1 {{ font-size: 2.2rem; font-weight: 800; margin: 0 0 8px 0; letter-spacing: -0.02em; }}
  .meta {{ color: var(--text-dim); font-size: 0.95rem; margin-bottom: 24px; }}

  .viz-container {{
    background: var(--card-bg);
    border-radius: 32px;
    border: 1px solid var(--border);
    padding: 24px;
    backdrop-filter: blur(12px);
  }}

  .controls {{
    display: flex;
    gap: 16px;
    align-items: center;
    margin-bottom: 24px;
    padding: 16px;
    background: rgba(0,0,0,0.3);
    border-radius: 16px;
  }}

  .timeline-slider {{
    flex: 1;
    -webkit-appearance: none;
    height: 8px;
    border-radius: 4px;
    background: rgba(99,102,241,0.3);
    outline: none;
  }}
  .timeline-slider::-webkit-slider-thumb {{
    -webkit-appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--primary);
    cursor: pointer;
  }}

  .btn {{
    padding: 10px 20px;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    background: var(--primary);
    color: white;
  }}
  .btn:hover {{ opacity: 0.9; }}
  .btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
  .btn-secondary {{ background: rgba(255,255,255,0.1); }}

  .timeline-info {{
    min-width: 300px;
    text-align: center;
    font-weight: 600;
  }}

  #graph {{
    width: 100%;
    height: 600px;
    border-radius: 16px;
    background: rgba(0,0,0,0.3);
  }}

  .node {{
    cursor: pointer;
  }}
  .node:hover {{
    stroke: white;
    stroke-width: 2px;
  }}
  .link {{
    stroke-opacity: 0.6;
  }}

  .stats {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-top: 24px;
  }}
  .stat-card {{
    background: rgba(0,0,0,0.3);
    padding: 16px;
    border-radius: 16px;
    text-align: center;
  }}
  .stat-value {{ font-size: 2rem; font-weight: 800; color: var(--primary); }}
  .stat-label {{ font-size: 0.85rem; color: var(--text-dim); }}
</style>
</head>
<body>
<nav>
  <div class="brand">REBUILD Evolution</div>
</nav>

<div class="content">
  <h1>{title}</h1>
  <div class="meta">{repo_path} &nbsp;·&nbsp; {len(snapshots)} snapshots</div>

  <div class="viz-container">
    <div class="controls">
      <button class="btn btn-secondary" id="prevBtn">◀ Previous</button>
      <button class="btn" id="playBtn">▶ Play</button>
      <button class="btn btn-secondary" id="nextBtn">Next ▶</button>
      <input type="range" class="timeline-slider" id="timelineSlider" min="0" max="{len(snapshots) - 1}" value="0">
      <div class="timeline-info">
        <span id="timestamp">Snapshot 1 / {len(snapshots)}</span>
        <div style="font-size: 0.75rem; color: var(--text-dim); margin-top: 4px;" id="commit"></div>
      </div>
    </div>

    <div id="graph"></div>

    <div class="stats">
      <div class="stat-card">
        <div class="stat-value" id="nodeCount">0</div>
        <div class="stat-label">Modules</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" id="edgeCount">0</div>
        <div class="stat-label">Dependencies</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" id="complexity">0</div>
        <div class="stat-label">Avg Complexity</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" id="loc">0</div>
        <div class="stat-label">Total LOC</div>
      </div>
    </div>
  </div>
</div>

<script>
const snapshots = {snapshots_js};
let currentIndex = 0;
let isPlaying = false;
let playInterval = null;

// Initialize graph
const svg = d3.select("#graph")
  .append("svg")
  .attr("width", "100%")
  .attr("height", "100%")
  .attr("viewBox", [0, 0, 1200, 600]);

const g = svg.append("g");

// Zoom behavior
const zoom = d3.zoom()
  .scaleExtent([0.1, 4])
  .on("zoom", (event) => g.attr("transform", event.transform));
svg.call(zoom);

function renderSnapshot(index) {{
  const snapshot = snapshots[index];
  if (!snapshot) return;

  // Clear previous
  g.selectAll("*").remove();

  // Create force simulation
  const nodes = snapshot.nodes.map(n => ({{
    id: n.name,
    ...n,
    x: Math.random() * 800 + 200,
    y: Math.random() * 400 + 100
  }}));
  const links = snapshot.edges.map(e => ({{
    source: e.source,
    target: e.target,
    ...e
  }}));

  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(100))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(600, 300))
    .force("collision", d3.forceCollide().radius(40));

  // Draw links
  const link = g.append("g")
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("class", "link")
    .attr("stroke", "#6366f1")
    .attr("stroke-width", 2);

  // Draw nodes
  const node = g.append("g")
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("class", "node")
    .attr("r", d => Math.max(10, Math.min(30, Math.sqrt(d.lines_of_code) / 2)))
    .attr("fill", d => {{
      if (d.complexity > 10) return "#ef4444";
      if (d.complexity > 5) return "#f97316";
      return "#6366f1";
    }})
    .call(drag(simulation));

  // Labels
  const labels = g.append("g")
    .selectAll("text")
    .data(nodes)
    .join("text")
    .text(d => d.name.split("/").pop())
    .attr("font-size", "12px")
    .attr("fill", "white")
    .attr("text-anchor", "middle")
    .attr("dy", 4);

  simulation.on("tick", () => {{
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    node
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);

    labels
      .attr("x", d => d.x)
      .attr("y", d => d.y);
  }});

  // Update stats
  document.getElementById("nodeCount").textContent = nodes.length;
  document.getElementById("edgeCount").textContent = links.length;
  const avgComplexity = nodes.length > 0
    ? (nodes.reduce((sum, n) => sum + (n.complexity || 0), 0) / nodes.length).toFixed(1)
    : 0;
  document.getElementById("complexity").textContent = avgComplexity;
  const totalLoc = nodes.reduce((sum, n) => sum + (n.lines_of_code || 0), 0);
  document.getElementById("loc").textContent = totalLoc;

  // Update info
  document.getElementById("timestamp").textContent = `Snapshot ${{index + 1}} / ${{snapshots.length}}`;
  document.getElementById("commit").textContent = snapshot.commit_sha ? snapshot.commit_sha.substring(0, 8) : "";
}}

function drag(simulation) {{
  function dragstarted(event) {{
    if (!event.active) simulation.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
  }}
  function dragged(event) {{
    event.subject.fx = event.x;
    event.subject.fy = event.y;
  }}
  function dragended(event) {{
    if (!event.active) simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
  }}
  return d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended);
}}

function updateIndex(newIndex) {{
  if (newIndex < 0 || newIndex >= snapshots.length) return;
  currentIndex = newIndex;
  document.getElementById("timelineSlider").value = currentIndex;
  renderSnapshot(currentIndex);
}}

// Event listeners
document.getElementById("timelineSlider").addEventListener("input", (e) => {{
  updateIndex(parseInt(e.target.value));
}});

document.getElementById("prevBtn").addEventListener("click", () => {{
  updateIndex(currentIndex - 1);
}});

document.getElementById("nextBtn").addEventListener("click", () => {{
  updateIndex(currentIndex + 1);
}});

document.getElementById("playBtn").addEventListener("click", () => {{
  isPlaying = !isPlaying;
  const btn = document.getElementById("playBtn");

  if (isPlaying) {{
    btn.textContent = "⏸ Pause";
    playInterval = setInterval(() => {{
      if (currentIndex >= snapshots.length - 1) {{
        currentIndex = 0;
      }}
      updateIndex(currentIndex + 1);
    }}, 2000);
  }} else {{
    btn.textContent = "▶ Play";
    clearInterval(playInterval);
  }}
}});

// Initial render
renderSnapshot(0);
</script>
</body>
</html>"""
