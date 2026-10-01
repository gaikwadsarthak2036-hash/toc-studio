// ---------------------------------------------------------------------------
// nfa.js — NFA Simulator
// Talks to POST /api/nfa/run (modules/nfa.py does the actual simulation).
// ---------------------------------------------------------------------------

(function () {
  const form = document.getElementById("nfaForm");
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
  const simLog = document.getElementById("simLog");
  const verdictBox = document.getElementById("verdict");
  const stepCounter = document.getElementById("stepCounter");

  const editor = TOCViz.createRowEditor(
    document.getElementById("transitionsEditor"),
    [
      { key: "from", label: "From", placeholder: "q0" },
      { key: "symbol", label: "Symbol", placeholder: "0" },
      { key: "to", label: "To (comma-separated)", placeholder: "q0, q1" },
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
      const response = await fetch("/api/nfa/run", {
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
      renderRun(data.table, data.result);
    } catch (err) {
      errorBox.textContent = "Couldn't reach the server. Please try again.";
    }
  });

  function renderRun(table, result) {
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

    verdictBox.innerHTML = `<span class="verdict ${result.accepted ? "accepted" : "rejected"}">${result.accepted ? "Accepted" : "Rejected"} &mdash; final active states: {${result.final_active_states.join(", ") || "&empty;"}}</span>`;

    // Step frames from the snapshots (one active-state-set per position)
    const frames = result.snapshots.map((active, i) => ({
      active,
      logIndex: i - 1,
    }));

    const logLines = result.log.map((entry, i) =>
      `<div data-line="${i}">Step ${i + 1}: {${entry.from.join(", ")}} --${entry.symbol}--&gt; {${entry.to.join(", ") || "&empty;"}}</div>`
    );
    if (logLines.length === 0) logLines.push('<div>No symbols to process (empty input string).</div>');
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
