// ---------------------------------------------------------------------------
// visualization.js
//
// Shared drawing helpers used across every automata module (DFA, NFA,
// epsilon-NFA, Regex, PDA, Turing Machine). Keeping this in one file means
// every simulator's diagrams, stacks and tapes share the same look.
// ---------------------------------------------------------------------------

const TOCViz = (function () {

  // ---- Circular auto-layout for a state diagram -----------------------
  // Given a list of state names and a list of {from, to, label} edges,
  // returns an SVG string with states positioned evenly around a circle.
  function renderAutomatonGraph(states, edges, opts) {
    opts = opts || {};
    const width = opts.width || 480;
    const height = opts.height || 380;
    const radius = Math.min(width, height) / 2 - 70;
    const cx = width / 2;
    const cy = height / 2;
    const finalStates = new Set(opts.finalStates || []);
    const startState = opts.startState || null;

    const positions = {};
    const n = states.length || 1;
    states.forEach((s, i) => {
      const angle = (2 * Math.PI * i) / n - Math.PI / 2;
      positions[s] = {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      };
    });

    // Group edges between the same pair of states so labels combine,
    // e.g. q0 --0,1--> q1 instead of two overlapping arrows.
    const grouped = {};
    edges.forEach((e) => {
      const key = e.from + "->" + e.to;
      grouped[key] = grouped[key] || { from: e.from, to: e.to, labels: [] };
      grouped[key].labels.push(e.label);
    });

    let svg = `<svg viewBox="0 0 ${width} ${height}" class="automaton-svg" xmlns="http://www.w3.org/2000/svg">`;
    svg += `<defs><marker id="viz-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--border-bright)"></path></marker>
            <marker id="viz-arrow-active" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--accent-cyan)"></path></marker></defs>`;

    // start arrow
    if (startState && positions[startState]) {
      const p = positions[startState];
      const angle = Math.atan2(p.y - cy, p.x - cx);
      const sx = p.x - 46 * Math.cos(angle);
      const sy = p.y - 46 * Math.sin(angle);
      const ex = p.x - 27 * Math.cos(angle);
      const ey = p.y - 27 * Math.sin(angle);
      svg += `<line x1="${sx}" y1="${sy}" x2="${ex}" y2="${ey}" stroke="var(--text-muted)" stroke-width="1.5" marker-end="url(#viz-arrow)"></line>`;
    }

    // edges (as curved paths so self-loops and reverse pairs are readable)
    Object.values(grouped).forEach((g) => {
      const label = g.labels.join(", ");
      const edgeId = "edge-" + g.from + "-" + g.to;
      if (g.from === g.to) {
        const p = positions[g.from];
        const loopPath = `M${p.x - 18},${p.y - 22} C${p.x - 60},${p.y - 80} ${p.x + 60},${p.y - 80} ${p.x + 18},${p.y - 22}`;
        svg += `<path id="${edgeId}" d="${loopPath}" fill="none" stroke="var(--border-bright)" stroke-width="1.5" marker-end="url(#viz-arrow)"></path>`;
        svg += `<text x="${p.x}" y="${p.y - 78}" text-anchor="middle" class="edge-label">${escapeXml(label)}</text>`;
      } else {
        const p1 = positions[g.from];
        const p2 = positions[g.to];
        const mx = (p1.x + p2.x) / 2;
        const my = (p1.y + p2.y) / 2;
        // perpendicular offset so A->B and B->A don't overlap
        const dx = p2.x - p1.x, dy = p2.y - p1.y;
        const len = Math.sqrt(dx * dx + dy * dy) || 1;
        const offx = (-dy / len) * 22;
        const offy = (dx / len) * 22;
        const curveX = mx + offx;
        const curveY = my + offy;

        const angle1 = Math.atan2(curveY - p1.y, curveX - p1.x);
        const angle2 = Math.atan2(curveY - p2.y, curveX - p2.x);
        const sx = p1.x + 27 * Math.cos(angle1);
        const sy = p1.y + 27 * Math.sin(angle1);
        const ex = p2.x + 27 * Math.cos(angle2);
        const ey = p2.y + 27 * Math.sin(angle2);

        svg += `<path id="${edgeId}" d="M${sx},${sy} Q${curveX},${curveY} ${ex},${ey}" fill="none" stroke="var(--border-bright)" stroke-width="1.5" marker-end="url(#viz-arrow)"></path>`;
        svg += `<text x="${curveX}" y="${curveY}" text-anchor="middle" class="edge-label">${escapeXml(label)}</text>`;
      }
    });

    // states
    states.forEach((s) => {
      const p = positions[s];
      const isFinal = finalStates.has(s);
      svg += `<g id="state-${cssSafe(s)}" class="automaton-state">`;
      svg += `<circle cx="${p.x}" cy="${p.y}" r="27"></circle>`;
      if (isFinal) svg += `<circle cx="${p.x}" cy="${p.y}" r="21" class="final-ring"></circle>`;
      svg += `<text x="${p.x}" y="${p.y + 5}" text-anchor="middle">${escapeXml(s)}</text>`;
      svg += `</g>`;
    });

    svg += `</svg>`;
    return svg;
  }

  function cssSafe(s) {
    return s.replace(/[^a-zA-Z0-9_-]/g, "_");
  }

  function escapeXml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function highlightStates(container, activeStateNames) {
    container.querySelectorAll(".automaton-state").forEach((el) => el.classList.remove("active"));
    (activeStateNames || []).forEach((s) => {
      const el = container.querySelector("#state-" + cssSafe(s));
      if (el) el.classList.add("active");
    });
  }

  function highlightEdge(container, fromState, toState) {
    container.querySelectorAll(".automaton-svg path[id^='edge-']").forEach((el) => {
      el.setAttribute("marker-end", "url(#viz-arrow)");
      el.classList.remove("active");
    });
    if (fromState == null || toState == null) return;
    const id = "edge-" + fromState + "-" + toState;
    const el = container.querySelector("#" + CSS.escape(id));
    if (el) {
      el.classList.add("active");
      el.setAttribute("marker-end", "url(#viz-arrow-active)");
    }
  }

  // ---- Generic Run / Step / Pause / Reset controller -------------------
  // frames: array of anything; onShow(frame, index) paints one frame.
  function createStepController(frames, onShow, opts) {
    opts = opts || {};
    const intervalMs = opts.intervalMs || 900;
    let index = 0;
    let timer = null;

    function show(i) {
      index = Math.max(0, Math.min(i, frames.length - 1));
      onShow(frames[index], index);
    }

    function step() {
      pause();
      if (index < frames.length - 1) show(index + 1);
    }

    function run() {
      pause();
      timer = setInterval(() => {
        if (index >= frames.length - 1) {
          pause();
          return;
        }
        show(index + 1);
      }, intervalMs);
    }

    function pause() {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
    }

    function reset() {
      pause();
      show(0);
    }

    show(0);

    return { step, run, pause, reset, get index() { return index; }, get frames() { return frames; } };
  }

  // ---- Stack renderer (for PDA) -----------------------------------------
  function renderStack(stackArray) {
    if (!stackArray || stackArray.length === 0) {
      return '<div class="stack-empty">empty</div>';
    }
    const items = stackArray.slice().reverse(); // top of stack drawn first
    return items.map((sym, i) =>
      `<div class="stack-cell${i === 0 ? " stack-top" : ""}">${escapeXml(sym)}</div>`
    ).join("");
  }

  // ---- Tape renderer (for Turing Machine) --------------------------------
  function renderTape(tapeArray, headIndex) {
    return tapeArray.map((sym, i) =>
      `<div class="tape-cell${i === headIndex ? " tape-head" : ""}">${escapeXml(sym)}</div>`
    ).join("");
  }

  // ---- Editable transitions table (add/remove rows) ---------------------
  // columns: [{key, label, placeholder}]. initialRows: [{key: value, ...}]
  function createRowEditor(container, columns, initialRows) {
    container.innerHTML = "";
    const table = document.createElement("table");
    table.className = "edit-table";
    const thead = document.createElement("thead");
    thead.innerHTML = "<tr>" + columns.map((c) => `<th>${escapeXml(c.label)}</th>`).join("") + "<th></th></tr>";
    const tbody = document.createElement("tbody");
    table.appendChild(thead);
    table.appendChild(tbody);
    container.appendChild(table);

    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.className = "btn btn-ghost add-row-btn";
    addBtn.textContent = "+ Add row";
    addBtn.addEventListener("click", () => addRow({}));
    container.appendChild(addBtn);

    function buildRowCells(row) {
      row = row || {};
      return columns.map((c) =>
        `<td><input type="text" data-key="${c.key}" value="${escapeXml(row[c.key] || "")}" placeholder="${escapeXml(c.placeholder || "")}"></td>`
      ).join("") + `<td><button type="button" class="row-remove" title="Remove row">&times;</button></td>`;
    }

    function addRow(row) {
      const tr = document.createElement("tr");
      tr.innerHTML = buildRowCells(row);
      tr.querySelector(".row-remove").addEventListener("click", () => tr.remove());
      tbody.appendChild(tr);
    }

    (initialRows && initialRows.length ? initialRows : [{}]).forEach(addRow);

    return {
      getRows() {
        return Array.from(tbody.querySelectorAll("tr")).map((tr) => {
          const obj = {};
          tr.querySelectorAll("input").forEach((inp) => { obj[inp.dataset.key] = inp.value; });
          return obj;
        });
      },
      setRows(rows) {
        tbody.innerHTML = "";
        (rows.length ? rows : [{}]).forEach(addRow);
      },
    };
  }

  // ---- Parse tree renderer (for CFG) -------------------------------------
  // tree: {symbol, children: [tree...] | null}
  function renderParseTree(tree, opts) {
    opts = opts || {};
    const levelHeight = 64;
    const nodeSpacing = 46;

    // First pass: assign each leaf an x-slot left-to-right, then position
    // internal nodes at the average of their children (classic simple
    // tree-layout approach -- good enough for the small grammars here).
    let nextX = 0;
    function layout(node, depth) {
      if (!node.children || node.children.length === 0) {
        const x = nextX * nodeSpacing;
        nextX += 1;
        return { symbol: node.symbol, x, y: depth * levelHeight, children: [], isLeaf: true };
      }
      const childNodes = node.children.map((c) => layout(c, depth + 1));
      const x = childNodes.reduce((sum, c) => sum + c.x, 0) / childNodes.length;
      return { symbol: node.symbol, x, y: depth * levelHeight, children: childNodes, isLeaf: false };
    }

    const positioned = layout(tree, 0);
    const width = Math.max(nextX * nodeSpacing, 200) + 60;
    const maxDepth = maxTreeDepth(positioned);
    const height = (maxDepth + 1) * levelHeight + 50;

    let svg = `<svg viewBox="0 0 ${width} ${height}" class="parse-tree-svg" xmlns="http://www.w3.org/2000/svg">`;

    function drawEdges(node) {
      node.children.forEach((c) => {
        svg += `<line class="tree-edge" x1="${node.x + 30}" y1="${node.y + 40}" x2="${c.x + 30}" y2="${c.y + 10}"></line>`;
        drawEdges(c);
      });
    }
    drawEdges(positioned);

    function drawNodes(node) {
      const cls = node.isLeaf ? "tree-node terminal" : "tree-node";
      svg += `<g class="${cls}"><circle cx="${node.x + 30}" cy="${node.y + 24}" r="18"></circle>`;
      svg += `<text x="${node.x + 30}" y="${node.y + 29}" text-anchor="middle">${escapeXml(node.symbol)}</text></g>`;
      node.children.forEach(drawNodes);
    }
    drawNodes(positioned);

    svg += `</svg>`;
    return svg;
  }

  function maxTreeDepth(node) {
    if (!node.children || node.children.length === 0) return 0;
    return 1 + Math.max(...node.children.map(maxTreeDepth));
  }

  return {
    renderAutomatonGraph,
    highlightStates,
    highlightEdge,
    createStepController,
    createRowEditor,
    renderStack,
    renderTape,
    renderParseTree,
    cssSafe,
    escapeXml,
  };
})();
