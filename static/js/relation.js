// ---------------------------------------------------------------------------
// relation.js — Relation & Function Simulator
// Talks to POST /api/relation/analyze and POST /api/relation/function
// (modules/relation.py does the actual checks).
// ---------------------------------------------------------------------------

(function () {
  // ---------------------------- Relation ----------------------------------
  const relForm = document.getElementById("relationForm");
  if (relForm) {
    const setAInput = document.getElementById("relSetA");
    const pairsInput = document.getElementById("relPairs");
    const errorBox = document.getElementById("relError");
    const resultsBox = document.getElementById("relResults");

    relForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.textContent = "";
      try {
        const response = await fetch("/api/relation/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ set_a: setAInput.value, pairs: pairsInput.value }),
        });
        const data = await response.json();
        if (!data.ok) {
          errorBox.textContent = data.error;
          resultsBox.hidden = true;
          return;
        }
        renderRelation(data.results);
      } catch (err) {
        errorBox.textContent = "Couldn't reach the server. Please try again.";
      }
    });

    function renderRelation(r) {
      resultsBox.hidden = false;
      document.getElementById("relPairsOut").textContent = r.pairs_formatted;

      const checks = [
        ["Reflexive", r.is_reflexive], ["Irreflexive", r.is_irreflexive],
        ["Symmetric", r.is_symmetric], ["Antisymmetric", r.is_antisymmetric],
        ["Transitive", r.is_transitive], ["Equivalence relation", r.is_equivalence],
        ["Partial order", r.is_partial_order],
      ];
      document.getElementById("relChecks").innerHTML = checks.map(([label, val]) =>
        `<div class="check-row"><span>${label}</span><span class="badge ${val ? "true" : "false"}">${val ? "True" : "False"}</span></div>`
      ).join("");

      // Matrix
      let mHtml = '<table class="matrix-table"><thead><tr><th></th>';
      r.elements.forEach((e) => { mHtml += `<th>${e}</th>`; });
      mHtml += "</tr></thead><tbody>";
      r.elements.forEach((e, i) => {
        mHtml += `<tr><th>${e}</th>`;
        r.matrix[i].forEach((v) => { mHtml += `<td class="${v ? "one" : "zero"}">${v}</td>`; });
        mHtml += "</tr>";
      });
      mHtml += "</tbody></table>";
      document.getElementById("matrixContainer").innerHTML = mHtml;

      // Graph (nodes + directed edges, no symbol labels needed)
      const edges = r.graph_edges.map(([a, b]) => ({ from: a, to: b, label: "" }));
      document.getElementById("relGraphContainer").innerHTML =
        TOCViz.renderAutomatonGraph(r.graph_nodes, edges, {});
    }
  }

  // ---------------------------- Function -----------------------------------
  const funcForm = document.getElementById("functionForm");
  if (funcForm) {
    const domainInput = document.getElementById("domain");
    const codomainInput = document.getElementById("codomain");
    const mappingInput = document.getElementById("mapping");
    const codomainCInput = document.getElementById("codomainC");
    const mappingGInput = document.getElementById("mappingG");
    const errorBox = document.getElementById("funcError");
    const resultsBox = document.getElementById("funcResults");

    funcForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.textContent = "";
      try {
        const response = await fetch("/api/relation/function", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            domain: domainInput.value,
            codomain: codomainInput.value,
            mapping: mappingInput.value,
            codomain_c: codomainCInput.value,
            mapping_g: mappingGInput.value,
          }),
        });
        const data = await response.json();
        if (!data.ok) {
          errorBox.textContent = data.error;
          resultsBox.hidden = true;
          return;
        }
        renderFunction(data.results, data.compose);
      } catch (err) {
        errorBox.textContent = "Couldn't reach the server. Please try again.";
      }
    });

    function mapToPairsText(mapping) {
      return "{" + Object.entries(mapping).map(([k, v]) => `${k}\u2192${v}`).join(", ") + "}";
    }

    function renderFunction(r, compose) {
      resultsBox.hidden = false;

      const checks = [
        ["Injective (one-one)", r.is_injective], ["Surjective (onto)", r.is_surjective],
        ["Bijective", r.is_bijective], ["Identity function", r.is_identity],
      ];
      document.getElementById("funcChecks").innerHTML = checks.map(([label, val]) =>
        `<div class="check-row"><span>${label}</span><span class="badge ${val ? "true" : "false"}">${val ? "True" : "False"}</span></div>`
      ).join("");

      document.getElementById("mappingOut").textContent = mapToPairsText(r.mapping);

      const inverseCard = document.getElementById("inverseCard");
      if (r.inverse) {
        inverseCard.hidden = false;
        document.getElementById("inverseOut").textContent = mapToPairsText(r.inverse);
      } else {
        inverseCard.hidden = true;
      }

      const composeSection = document.getElementById("composeSection");
      if (compose) {
        composeSection.hidden = false;
        const gChecks = [
          ["g is injective", compose.g_analysis.is_injective],
          ["g is surjective", compose.g_analysis.is_surjective],
          ["g is bijective", compose.g_analysis.is_bijective],
        ];
        document.getElementById("gChecks").innerHTML = gChecks.map(([label, val]) =>
          `<div class="check-row"><span>${label}</span><span class="badge ${val ? "true" : "false"}">${val ? "True" : "False"}</span></div>`
        ).join("");
        document.getElementById("composedOut").textContent = mapToPairsText(compose.composed);
      } else {
        composeSection.hidden = true;
      }
    }
  }

})();
