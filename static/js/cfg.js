// ---------------------------------------------------------------------------
// cfg.js — CFG Simulator
// Talks to POST /api/cfg/derive (modules/cfg.py searches for a derivation).
// ---------------------------------------------------------------------------

(function () {
  const form = document.getElementById("cfgForm");
  if (!form) return;

  const grammarInput = document.getElementById("grammar");
  const inputStringInput = document.getElementById("inputString");
  const errorBox = document.getElementById("formError");
  const resultsBox = document.getElementById("results");
  const verdictBox = document.getElementById("verdict");
  const leftmostList = document.getElementById("leftmostList");
  const rightmostList = document.getElementById("rightmostList");
  const treeContainer = document.getElementById("treeContainer");

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      grammarInput.value = chip.dataset.grammar;
      inputStringInput.value = chip.dataset.input;
      form.requestSubmit();
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.textContent = "";

    try {
      const response = await fetch("/api/cfg/derive", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grammar: grammarInput.value, input_string: inputStringInput.value }),
      });
      const data = await response.json();
      if (!data.ok) {
        errorBox.textContent = data.error;
        resultsBox.hidden = true;
        return;
      }
      renderResult(data.result);
    } catch (err) {
      errorBox.textContent = "Couldn't reach the server. Please try again.";
    }
  });

  function renderResult(r) {
    resultsBox.hidden = false;

    if (!r.found) {
      verdictBox.innerHTML = `<span class="verdict rejected">String Rejected &mdash; no derivation found within the search limit</span>`;
      leftmostList.innerHTML = "<p>No derivation found.</p>";
      rightmostList.innerHTML = "<p>No derivation found.</p>";
      treeContainer.innerHTML = "";
      return;
    }

    verdictBox.innerHTML = `<span class="verdict accepted">String Accepted</span>`;

    const steps = [r.start_symbol, ...r.steps.map((s) => s.form)];
    leftmostList.innerHTML = steps.map((s, i) =>
      i === 0 ? s : `<span class="arrow">&#8658;</span>${s} <span style="color:var(--text-faint);font-size:0.78rem;">(${r.steps[i - 1].production})</span>`
    ).join("<br>");

    const rSteps = [r.start_symbol, ...r.rightmost_steps.map((s) => s.form)];
    rightmostList.innerHTML = rSteps.map((s, i) =>
      i === 0 ? s : `<span class="arrow">&#8658;</span>${s} <span style="color:var(--text-faint);font-size:0.78rem;">(${r.rightmost_steps[i - 1].production})</span>`
    ).join("<br>");

    treeContainer.innerHTML = TOCViz.renderParseTree(r.parse_tree);
  }

  if (grammarInput.value.trim() === "") {
    grammarInput.value = "S -> aSb | eps";
    inputStringInput.value = "aaabbb";
    form.requestSubmit();
  }
})();
