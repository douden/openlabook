// ----------------------------------
// 1) Setup SVG and container
// ----------------------------------
const vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
const width = vw;
const height = vh;
const maxdim = Math.max(width, height);

const svg = d3.select("#graph").attr("width", width).attr("height", height);

// Create a common container for both hulls and the rest of the graph.
const container = svg.append("g");
// Hulls will be rendered in this layer (behind nodes).
const hullGroup = container.append("g").attr("class", "hullLayer");
// Nodes, links, and labels will be rendered here.
const gContainer = container.append("g");

// ----------------------------------
// 2) Define the zoom behavior
//    and handle sessionStorage
// ----------------------------------
const zoom = d3.zoom()
  .extent([[0, 0], [width, height]])
  .scaleExtent([0.5, 5])
  .on("zoom", (event) => {
    container.attr("transform", event.transform);
    // Save the transform to sessionStorage
    sessionStorage.setItem('graphTransform', JSON.stringify(event.transform));
  });

// Check if there's a previously saved transform in sessionStorage
const savedTransform = sessionStorage.getItem('graphTransform');

// ----------------------------------
// 3) Helper functions
// ----------------------------------
function capitalizeWords(str) {
  return str.replace(/\b\w/g, char => char.toUpperCase());
}
function extractTitle(filename) {
  return capitalizeWords(filename.replace('.md', '').replace(/_/g, ' '));
}

// Margin for hull expansion.
const visualMargin = maxdim * 0.025;

function validateColorName(color) {
  var style = new Option().style;
  style.color = color;
 
  // Check if the computed color is the same as the input color
  return style.color == color;
 }

// Dummy dictionary mapping tag values (in lowercase) to colors.
const groupColors = {
  // <groupColors>
};

for (group in groupColors) {
  console.log(validateColorName(groupColors[group]))
}

// Utility: Compute an expanded convex hull for a set of nodes given a margin.
function computeExpandedHull(groupNodes, margin) {
  if (groupNodes.length < 3) return null;
  const step = Math.PI / 36;
  const expandedPoints = [];
  groupNodes.forEach(d => {
    for (let angle = 0; angle < 2 * Math.PI; angle += step) {
      const x = d.x + margin * Math.cos(angle);
      const y = d.y + margin * Math.sin(angle);
      expandedPoints.push([x, y]);
    }
  });
  return d3.polygonHull(expandedPoints);
}

// ----------------------------------
// 4) Node-position persistence
//    - Save & load positions
// ----------------------------------
function saveNodePositions(nodes) {
  const currentPositions = nodes.map(n => ({
    id: n.id,
    x: n.x,
    y: n.y,
    fx: n.fx,
    fy: n.fy
  }));
  sessionStorage.setItem('nodePositions', JSON.stringify(currentPositions));
}

function restoreNodePositions(nodes) {
  const savedPositions = sessionStorage.getItem('nodePositions');
  if (!savedPositions) return false;

  try {
    const positions = JSON.parse(savedPositions);
    // Create a map (id -> position data) for quick lookup
    const posMap = new Map(positions.map(p => [p.id, p]));

    let restoredCount = 0;
    nodes.forEach(n => {
      const saved = posMap.get(n.id);
      if (saved) {
        // Assign the saved coords so the simulation will start from here
        n.x = saved.x;
        n.y = saved.y;
        // If the node was pinned, restore that
        n.fx = saved.fx;
        n.fy = saved.fy;
        restoredCount++;
      }
    });

    return restoredCount > 0;  // if we restored at least one node
  } catch (err) {
    console.warn("Failed to parse node positions:", err);
    return false;
  }
}

// ----------------------------------
// 5) Fetch references and tags
// ----------------------------------
Promise.all([
  fetch('/_static/<references.txt>').then(response => response.text()),
  fetch('/_static/<groups.txt>').then(response => response.text())
])
.then(([refData, tagData]) => {
  // Parse tags.txt into a map: filename -> tag.
  const tagMap = new Map();
  tagData.trim().split('\n').forEach(line => {
    // Expected format: "filename.md -> [tag: 'tag value']"
    const m = line.match(/^(.*?) -> \[tag:\s*'(.*?)'\]$/);
    if (m) {
      tagMap.set(m[1].trim(), m[2].trim());
    }
  });
  
  // Parse references.txt
  const lines = refData.trim().split('\n');
  const nodesMap = new Map();
  const links = [];
  const referenceCounts = new Map();

  lines.forEach(line => {
    // Expected format: "source.md -> [text: 'Display'] [target: 'target']"
    const match = line.match(/^(.*?) -> \[text: '(.*?)'\] \[target: '(.*?)'\]$/);
    if (match) {
      const sourceFile = match[1].trim();
      const displayText = match[2].trim();
      const target = match[3].trim();

      if (!nodesMap.has(sourceFile)) {
        nodesMap.set(sourceFile, {
          id: sourceFile,
          text: extractTitle(sourceFile),
          link: `/${sourceFile.replace('.md', '.html')}`
        });
      }
      if (!nodesMap.has(target + '.md')) {
        nodesMap.set(target + '.md', {
          id: target + '.md',
          text: extractTitle(target),
          link: `/${target}.html`
        });
      }

      links.push({ source: sourceFile, target: target + '.md' });

      referenceCounts.set(target + '.md', (referenceCounts.get(target + '.md') || 0) + 1);
      referenceCounts.set(sourceFile, (referenceCounts.get(sourceFile) || 0) + 1);
    }
  });

  // Add nodes from tags.txt that are not in references.txt.
  tagMap.forEach((tag, filename) => {
    if (!nodesMap.has(filename)) {
      nodesMap.set(filename, { 
        id: filename,
        text: extractTitle(filename),
        link: `/${filename.replace('.md', '.html')}`,
        tag: tag
      });
      referenceCounts.set(filename, 0);
    }
  });

  // Build the final list of nodes
  const nodes = Array.from(nodesMap.values());
  // Ensure each node has its tag property if available.
  nodes.forEach(node => {
    if (!node.tag && tagMap.has(node.id)) {
      node.tag = tagMap.get(node.id);
    }
  });

  // Assign node radii based on reference counts
  const minRadius = maxdim * 0.01;
  const maxRadius = maxdim * 0.01;
  const maxReferences = 10;
  nodes.forEach(node => {
    const count = referenceCounts.get(node.id) || 0;
    node.radius = minRadius + (maxRadius - minRadius) * Math.min(count / maxReferences, 1);
  });

  // ----------------------------------
  // 6) Optionally restore positions
  //    so the sim starts from the latest known state
  // ----------------------------------
  const hadSavedPositions = restoreNodePositions(nodes);

  // Create the force simulation
  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(maxdim * 0.1))
    .force("charge", d3.forceManyBody().strength(-maxdim / 2).distanceMax(maxdim * 0.25))
    .force("center", d3.forceCenter(width / 2, height / 2).strength(0.1))
    .on("tick", ticked)
    .on("end", () => {
      // Once the simulation ends, store final positions
      saveNodePositions(nodes);
    });

  // If we did restore positions, let’s start from a lower alpha so it doesn’t drastically rearrange.
  // But it WILL continue to run.
  if (hadSavedPositions) {
    // You can tweak this alpha to control how much the existing layout changes
    simulation.alpha(0.3).restart(); 
  } else {
    // Normal start
    simulation.alpha(1).restart();
  }

  // Create the links
  const link = gContainer.selectAll(".link")
    .data(links)
    .enter()
    .append("line")
    .attr("class", "link");

  // Create node elements
  const node = gContainer.selectAll(".node")
    .data(nodes)
    .enter()
    .append("circle")
    .attr("class", d => {
      let classes = "node";
      if (d.tag) {
        const tagClass = d.tag.toLowerCase().replace(/\s+/g, '-');
        classes += " " + tagClass;
      }
      return classes;
    })
    .attr("r", d => d.radius)
    .style("fill", d => {
      if (d.tag) {
        return groupColors[d.tag.toLowerCase()] || "#ccc";
      } else {
        return "#ccc";
      }
    })
    .call(d3.drag()
      .on("start", dragStarted)
      .on("drag", dragged)
      .on("end", dragEnded)
    )
    .on("click", (event, d) => {
      if (d.link) window.open(d.link, "_top");
    });

  // Create labels
  const label = gContainer.selectAll(".label")
    .data(nodes)
    .enter()
    .append("text")
    .style("font-size", (maxdim * 0.01) + "px")
    .attr("class", "label")
    .attr("text-anchor", "middle")
    .attr("dy", d => -d.radius - 5)
    .text(d => d.text);

  function ticked() {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    node
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);

    label
      .attr("x", d => d.x)
      .attr("y", d => d.y);
    
    // --- Compute and render hulls for each tag group ---
    const groups = d3.group(nodes.filter(d => d.tag), d => d.tag);
    const hullData = [];
    groups.forEach((groupNodes, tag) => {
       if (groupNodes.length >= 3) {
         const hull = computeExpandedHull(groupNodes, visualMargin);
         if (hull) {
           hullData.push({ tag: tag, hull: hull });
         }
       }
    });
    
    const hullPaths = hullGroup.selectAll("path")
        .data(hullData, d => d.tag);
    
    hullPaths.enter()
      .append("path")
      .attr("class", d => "hull " + d.tag.toLowerCase().replace(/\s+/g, "-"))
      .merge(hullPaths)
      .attr("d", d => "M" + d.hull.join("L") + "Z")
      .style("fill", d => groupColors[d.tag.toLowerCase()] || "#ccc")
      .style("stroke", "#999")
      .style("opacity", 0.3);
    
    hullPaths.exit().remove();
    // --- End hull rendering ---
  }

  // --- Drag handlers ---
  function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }
  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }
  function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
    // Save positions again, to capture the user's drag
    saveNodePositions(nodes);
  }

  // ----------------------------------
  // 7) Call the zoom on the SVG,
  //    then apply any saved transform
  // ----------------------------------
  svg.call(zoom);

  if (savedTransform) {
    try {
      const t = JSON.parse(savedTransform);
      // Construct a D3 ZoomIdentity with the stored translate (x,y) and scale (k)
      const restored = d3.zoomIdentity.translate(t.x, t.y).scale(t.k);
      // Apply it
      svg.call(zoom.transform, restored);
    } catch (err) {
      console.warn("Could not parse saved zoom transform:", err);
    }
  }
})
.catch(err => console.error('Failed to load references or tags:', err));