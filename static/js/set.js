// ---------------------------------------------------------------------------
// set.js — Set Operations Simulator
//
// Talks to POST /api/set/compute, which does the actual parsing and set
// math in Python (see modules/set_operations.py). This file's only job is
// to send the two text inputs, and paint whatever comes back.
// ---------------------------------------------------------------------------

(function () {
  const form = document.getElementById("setForm");
  if (!form) return; // not on the Set page

  const setAInput = document.getElementById("setA");
  const setBInput = document.getElementById("setB");
  const errorBox = document.getElementById("formError");
  const resultsBox = document.getElementById("results");

  // ---- Example chips -----------------------------------------------------
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      setAInput.value = chip.dataset.setA;
      setBInput.value = chip.dataset.setB;
      form.requestSubmit();
    });
  });

  // ---- Form submit --------------------------------------------------------
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.textContent = "";

    try {
      const response = await fetch("/api/set/compute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          set_a: setAInput.value,
          set_b: setBInput.value,
        }),
      });

      const payload = await response.json();

      if (!payload.ok) {
        errorBox.textContent = payload.error || "That input couldn't be read. Please check the format.";
        resultsBox.hidden = true;
        return;
      }

      renderResults(payload.results);
    } catch (err) {
      errorBox.textContent = "Couldn't reach the server. Please try again.";
      resultsBox.hidden = true;
    }
  });

  function renderResults(r) {
    setText("out-set-a", r.set_a);
    setText("out-set-b", r.set_b);
    setText("out-union", r.union);
    setText("out-intersection", r.intersection);
    setText("out-diff-ab", r.difference_ab);
    setText("out-diff-ba", r.difference_ba);
    setText("out-symdiff", r.symmetric_difference);
    setText("out-cartesian", r.cartesian_product);

    setBadge("chk-a-sub-b", r.is_a_subset_of_b);
    setBadge("chk-b-sub-a", r.is_b_subset_of_a);
    setBadge("chk-a-propersub-b", r.is_a_proper_subset_of_b);
    setBadge("chk-b-propersub-a", r.is_b_proper_subset_of_a);
    setBadge("chk-a-super-b", r.is_a_superset_of_b);
    setBadge("chk-b-super-a", r.is_b_superset_of_a);

    setText("out-powerset-a", r.power_set_a);
    setText("out-powerset-a-size", r.power_set_a_size);
    setText("out-powerset-b", r.power_set_b);
    setText("out-powerset-b-size", r.power_set_b_size);

    renderVisualizations(r);
    resultsBox.hidden = false;
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function setBadge(id, isTrue) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = isTrue ? "True" : "False";
    el.classList.remove("true", "false");
    el.classList.add(isTrue ? "true" : "false");
  }


  // ---- Set operation visualizations --------------------------------------
  function renderVisualizations(r) {
    const host = document.getElementById("setVisualizations");
    if (!host) return;

    const cards = [
      ["Union", "A ∪ B", "union", r.union_elements],
      ["Intersection", "A ∩ B", "intersection", r.intersection_elements],
      ["Difference", "A − B", "difference-ab", r.difference_ab_elements],
      ["Reverse Difference", "B − A", "difference-ba", r.difference_ba_elements],
      ["Symmetric Difference", "A △ B", "symmetric", r.symmetric_difference_elements]
    ];

    host.innerHTML = cards.map(([title, notation, kind, result]) =>
      `<div class="set-viz-card">
        <div class="set-viz-title"><strong>${title}</strong><span>${notation}</span></div>
        ${vennSvg(r.elements_a, r.elements_b, result, kind)}
        <div class="viz-result">Result: <span>${escapeHtml(formatElements(result))}</span></div>
      </div>`
    ).join("");

    host.innerHTML += `
      <div class="set-viz-card set-viz-wide">
        <div class="set-viz-title"><strong>Cartesian Product</strong><span>A × B</span></div>
        ${cartesianSvg(r.elements_a, r.elements_b, r.cartesian_pairs)}
        <div class="viz-result">Pairs: <span>${r.cartesian_pairs.length}</span> (${r.elements_a.length} × ${r.elements_b.length})</div>
      </div>
      <div class="set-viz-card">
        <div class="set-viz-title"><strong>Subset / Superset</strong><span>Containment</span></div>
        ${containmentSvg(r)}
      </div>
      <div class="set-viz-card">
        <div class="set-viz-title"><strong>Power Set Size</strong><span>P(A), P(B)</span></div>
        ${powerSetSvg(r)}
      </div>`;
  }

  function vennSvg(a, b, result, kind) {
    // Filter first: only elements of the selected operation's result are drawn.
    const res = result.map(String);
    const inA = new Set(a.map(String)), inB = new Set(b.map(String));
    const onlyA = res.filter(x => inA.has(x) && !inB.has(x));
    const both = res.filter(x => inA.has(x) && inB.has(x));
    const onlyB = res.filter(x => !inA.has(x) && inB.has(x));

    function chips(items, x, y) {
      const max = 10;
      const shown = items.slice(0, max).map((v, i) => {
        const row = Math.floor(i / 5), col = i % 5;
        return `<text x="${x + col * 30}" y="${y + row * 24}" class="viz-element selected">${escapeHtml(v)}</text>`;
      }).join("");
      const more = items.length > max
        ? `<text x="${x}" y="${y + 2 * 24}" class="viz-element">+${items.length - max} more</text>` : "";
      return shown + more;
    }
    return `<svg class="set-viz-svg venn-svg" viewBox="0 0 430 190" role="img" aria-label="${kind} Venn diagram">
      <circle cx="170" cy="88" r="68" class="venn-circle ${kind === "difference-ba" ? "" : "focus"}"></circle>
      <circle cx="260" cy="88" r="68" class="venn-circle ${kind === "difference-ab" ? "" : "focus"}"></circle>
      <text x="120" y="27" class="set-label">A</text><text x="302" y="27" class="set-label">B</text>
      ${chips(onlyA, 112, 72)}
      ${chips(both, 202, 72)}
      ${chips(onlyB, 292, 72)}
    </svg>`;
  }

  function cartesianSvg(a, b, pairs) {
    const max = 50, shownA = a.slice(0, max), shownB = b.slice(0, max);
    const pairSet = new Set(pairs.map(p => String(p[0]) + "\u0000" + String(p[1])));
    let svg = `<svg class="set-viz-svg cartesian-svg" viewBox="0 0 520 250" role="img" aria-label="Cartesian product grid">`;
    const left = 95, top = 45, cellW = Math.min(390 / Math.max(shownB.length, 1), 34), cellH = Math.min(165 / Math.max(shownA.length, 1), 24);
    svg += `<text x="18" y="24" class="set-label">A × B</text>`;
    shownB.forEach((v,j) => svg += `<text x="${left + j*cellW + cellW/2}" y="39" text-anchor="middle" class="axis-label">${escapeHtml(String(v))}</text>`);
    shownA.forEach((v,i) => {
      svg += `<text x="82" y="${top + i*cellH + cellH/2 + 4}" text-anchor="end" class="axis-label">${escapeHtml(String(v))}</text>`;
      shownB.forEach((w,j) => {
        const active = pairSet.has(String(v) + "\u0000" + String(w));
        svg += `<rect x="${left+j*cellW}" y="${top+i*cellH}" width="${Math.max(cellW-2,3)}" height="${Math.max(cellH-2,3)}" rx="3" class="${active ? "pair-cell active" : "pair-cell"}"></rect>`;
      });
    });
    svg += `</svg>`;
    return svg;
  }

  function containmentSvg(r) {
    const aSub = r.is_a_subset_of_b, bSub = r.is_b_subset_of_a;
    return `<svg class="set-viz-svg containment-svg" viewBox="0 0 430 170">
      <circle cx="150" cy="85" r="${aSub ? 52 : 62}" class="contain-circle ${aSub ? "selected" : ""}"></circle>
      <circle cx="${aSub ? 150 : 280}" cy="85" r="${aSub ? 78 : 62}" class="contain-circle"></circle>
      <text x="150" y="89" text-anchor="middle" class="set-label">A</text>
      <text x="${aSub ? 150 : 280}" y="89" text-anchor="middle" class="set-label">B</text>
      <text x="215" y="145" text-anchor="middle" class="contain-caption">${aSub ? "A ⊆ B" : bSub ? "B ⊆ A" : "Neither is a subset"}</text>
    </svg>`;
  }

  function powerSetSvg(r) {
    const a = Number(r.power_set_a_size), b = Number(r.power_set_b_size);
    const scale = Math.max(a, b, 1);
    return `<div class="power-bars">
      <div><span>P(A)</span><div class="power-track"><i style="width:${Math.max(4, a/scale*100)}%"></i></div><b>${a.toLocaleString()} subsets</b></div>
      <div><span>P(B)</span><div class="power-track"><i style="width:${Math.max(4, b/scale*100)}%"></i></div><b>${b.toLocaleString()} subsets</b></div>
      <small>Power set size = 2ⁿ. Full enumeration is shown only for sets up to 12 elements.</small>
    </div>`;
  }

  function formatElements(arr) {
    if (!arr || !arr.length) return "∅";
    return "{" + arr.join(", ") + "}";
  }

  function escapeHtml(value) {
    return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // Run once on page load with the default values already in the inputs.
  form.requestSubmit();
})();
