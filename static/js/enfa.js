// ---------------------------------------------------------------------------
// enfa.js — epsilon-NFA Simulator
// Talks to POST /api/enfa/run (modules/enfa.py does the actual simulation).
// ---------------------------------------------------------------------------

(function () {
  const form = document.getElementById("enfaForm");
  if (!form) return;

  const statesInput = document.getElementById("states");
  const alphabetInput = document.getElementById("alphabet");
  const startInput = document.getElementById("startState");
  const finalInput = document.getElementById("finalStates");
  const inputStringInput = document.getElementById("inputString");
  const errorBox = document.getElementById("formError");
  const resultsBox = document.getElementById("results");
  const graphContainer = document.getElementById("graphContainer");
  const tableContainer = document.getElementById("tableContainer");
  const closureGrid = document.getElementById("closureGrid");
  const nfaConversionContainer = document.getElementById("nfaConversionContainer");
  const simLog = document.getElementById("simLog");
  const verdictBox = document.getElementById("verdict");
  const stepCounter = document.getElementById("stepCounter");

  const editor = TOCViz.createRowEditor(
    document.getElementById("transitionsEditor"),
    [
      { key: "from", label: "From", placeholder: "q0" },
      { key: "symbol", label: "Symbol (or eps)", placeholder: "eps" },
      { key: "to", label: "To (comma-separated)", placeholder: "q1" },
    ],
    []
  );

  let controller = null;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.textContent = "";

    const payload = {
      states: statesInput.value,
      alphabet: alphabetInput.value,
      start_state: startInput.value,
      final_states: finalInput.value,
      input_string: inputStringInput.value,
      transitions: editor.getRows(),
    };

    try {
      const response = await fetch("/api/enfa/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!data.ok) {
        errorBox.textContent = data.error;
        resultsBox.hidden = true;
        return;
      }
      renderRun(data);
    } catch (err) {
      errorBox.textContent = "Couldn't reach the server. Please try again.";
    }
  });

  function renderRun(data) {
    const { table, closures, nfa_conversion, result } = data;
    resultsBox.hidden = false;

    graphContainer.innerHTML = TOCViz.renderAutomatonGraph(table.states, table.edges, {
      startState: table.start_state,
      finalStates: table.final_states,
    });

    let html = '<table class="transition-table"><thead><tr><th>State</th>';
    table.alphabet.forEach((sym) => { html += `<th>${sym}</th>`; });
    html += "</tr></thead><tbody>";
    table.rows.forEach((row) => {
      const isStart = row.state === table.start_state;
      const isFinal = table.final_states.includes(row.state);
      html += `<tr class="${isStart ? "tt-start" : ""} ${isFinal ? "tt-final" : ""}"><td class="state-cell">${row.state}</td>`;
      table.alphabet.forEach((sym) => { html += `<td>${row.cells[sym]}</td>`; });
      html += "</tr>";
    });
    html += "</tbody></table>";
    tableContainer.innerHTML = html;

    closureGrid.innerHTML = Object.entries(closures).map(([state, closure]) =>
      `<div class="check-row"><span>closure(${state})</span><span class="mono">{${closure.join(", ")}}</span></div>`
    ).join("");

    let convHtml = '<table class="transition-table"><thead><tr><th>State</th>';
    nfa_conversion.alphabet.forEach((sym) => { convHtml += `<th>${sym}</th>`; });
    convHtml += "</tr></thead><tbody>";
    nfa_conversion.states.forEach((s) => {
      const isStart = s === nfa_conversion.start_state;
      const isFinal = nfa_conversion.final_states.includes(s);
      convHtml += `<tr class="${isStart ? "tt-start" : ""} ${isFinal ? "tt-final" : ""}"><td class="state-cell">${s}</td>`;
      nfa_conversion.alphabet.forEach((sym) => {
        const targets = nfa_conversion.transitions[s + "|" + sym];
        convHtml += `<td>${targets ? "{" + targets.join(", ") + "}" : "&empty;"}</td>`;
      });
      convHtml += "</tr>";
    });
    convHtml += "</tbody></table>";
    nfaConversionContainer.innerHTML = convHtml;

    verdictBox.innerHTML = `<span class="verdict ${result.accepted ? "accepted" : "rejected"}">${result.accepted ? "Accepted" : "Rejected"} &mdash; final active states: {${result.final_active_states.join(", ") || "&empty;"}}</span>`;

    const frames = result.snapshots.map((active, i) => ({ active, logIndex: i - 1 }));

    const logLines = result.log.map((entry, i) => {
      if (entry.stage === "start + \u03b5-closure") {
        return `<div data-line="${i}">Start + \u03b5-closure: {${entry.active.join(", ")}}</div>`;
      }
      return `<div data-line="${i}">Step ${i}: consume "${entry.symbol}" \u2192 {${entry.moved_to.join(", ") || "&empty;"}} \u2192 \u03b5-closure {${entry.active.join(", ") || "&empty;"}}</div>`;
    });
    simLog.innerHTML = logLines.join("");

    function onShow(frame, index) {
      TOCViz.highlightStates(graphContainer, frame.active);
      simLog.querySelectorAll("div").forEach((el) => el.classList.remove("current-line"));
      if (frame.logIndex >= 0) {
        const line = simLog.querySelector(`[data-line="${frame.logIndex}"]`);
        if (line) { line.classList.add("current-line"); line.scrollIntoView({ block: "nearest" }); }
      }
      stepCounter.textContent = `Step ${index} / ${frames.length - 1}`;
    }

    if (controller) controller.pause();
    controller = TOCViz.createStepController(frames, onShow);
  }

  document.getElementById("btnStep").addEventListener("click", () => controller && controller.step());
  document.getElementById("btnRun").addEventListener("click", () => controller && controller.run());
  document.getElementById("btnPause").addEventListener("click", () => controller && controller.pause());
  document.getElementById("btnReset").addEventListener("click", () => controller && controller.reset());

})();
