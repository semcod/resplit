import json
from pathlib import Path
from typing import Dict, List
from .service_graph import ServiceNode

class GraphExporter:
    """
    Exports ServiceGraph to an interactive D3.js HTML visualization.
    """
    def __init__(self, nodes: Dict[str, ServiceNode]):
        self.nodes = nodes

    def export_html(self, output_path: Path):
        data = self._prepare_d3_data()
        
        template = """
<!DOCTYPE html>
<html>
<head>
    <title>Rebuild Architecture Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: #f8fafc; margin: 0; overflow: hidden; }
        .node circle { stroke: #334155; stroke-width: 2px; }
        .node text { font-size: 12px; fill: #94a3b8; pointer-events: none; }
        .link { stroke: #334155; stroke-opacity: 0.6; stroke-width: 1.5px; fill: none; }
        .tooltip { position: absolute; background: rgba(30, 41, 59, 0.9); border: 1px solid #475569; padding: 10px; border-radius: 6px; font-size: 13px; display: none; }
        h1 { position: absolute; top: 20px; left: 20px; font-weight: 300; color: #38bdf8; margin: 0; }
    </style>
</head>
<body>
    <h1>Architecture Graph</h1>
    <div id="tooltip" class="tooltip"></div>
    <svg width="100%" height="100vh"></svg>

    <script>
        const data = """ + json.dumps(data) + """;
        const svg = d3.select("svg");
        const width = window.innerWidth;
        const height = window.innerHeight;
        const g = svg.append("g");

        const zoom = d3.zoom().on("zoom", (e) => g.attr("transform", e.transform));
        svg.call(zoom);

        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = g.append("g").selectAll("line")
            .data(data.links)
            .enter().append("line")
            .attr("class", "link")
            .attr("marker-end", "url(#arrowhead)");

        svg.append("defs").append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "-0 -5 10 10")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("orient", "auto")
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .append("svg:path")
            .attr("d", "M 0,-5 L 10 ,0 L 0,5")
            .attr("fill", "#334155");

        const node = g.append("g").selectAll(".node")
            .data(data.nodes)
            .enter().append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", 8)
            .attr("fill", d => d.id.includes("service") ? "#38bdf8" : "#818cf8")
            .on("mouseover", (e, d) => {
                const tt = d3.select("#tooltip");
                tt.style("display", "block")
                  .html(`<b>${d.id}</b><br>${d.methods.length} methods<br><br>${d.methods.slice(0,5).join('<br>')}`)
                  .style("left", (e.pageX + 10) + "px")
                  .style("top", (e.pageY + 10) + "px");
            })
            .on("mouseout", () => d3.select("#tooltip").style("display", "none"));

        node.append("text")
            .attr("dx", 12)
            .attr("dy", ".35em")
            .text(d => d.id.split('.').pop());

        simulation.on("tick", () => {
            link.attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            node.attr("transform", d => `translate(${d.x},${d.y})`);
        });

        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }
        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }
        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }
    </script>
</body>
</html>
        """
        output_path.write_text(template)

    def _prepare_d3_data(self) -> Dict:
        nodes = []
        links = []
        
        # Add primary nodes
        for name, node in self.nodes.items():
            nodes.append({
                "id": name,
                "methods": node.methods,
                "group": 1 if "service" in name else 2
            })
            
            # Add links
            for dep in node.dependencies:
                if dep in self.nodes:
                    links.append({
                        "source": name,
                        "target": dep,
                        "value": 1
                    })
        
        return {"nodes": nodes, "links": links}
