// ---------------------------------------------------------------------------
// regex.js — Regular Expression Simulator
// Talks to POST /api/regex/test (modules/regex.py compiles + simulates).
// ---------------------------------------------------------------------------

(function () {
  const form = document.getElementById("regexForm");
  if (!form) return;

  const patternInput = document.getElementById("pattern");
  const inputStringInput = document.getElementById("inputString");
  const errorBox = document.getElementById("formError");
  const resultsBox = document.getElementById("results");
  const graphContainer = document.getElementById("graphContainer");
  const tableContainer = document.getElementById("tableContainer");
  const simLog = document.getElementById("simLog");
  const verdictBox = document.getElementById("verdict");
  const stepCounter = document.getElementById("stepCounter");

  let controller = null;

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      patternInput.value = chip.dataset.pattern;
      inputStringInput.value = chip.dataset.input;
      form.requestSubmit();
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.textContent = "";

    try {
      const response = await fetch("/api/regex/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pattern: patternInput.value, input_string: inputStringInput.value }),
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
    const { table, start_state, final_states, result } = data;
    resultsBox.hidden = false;

    graphContainer.innerHTML = TOCViz.renderAutomatonGraph(table.states, table.edges, {
      startState: start_state,
      finalStates: final_states,
    });

    let html = '<table class="transition-table"><thead><tr><th>State</th>';
    table.alphabet.forEach((sym) => { html += `<th>${sym}</th>`; });
    html += "</tr></thead><tbody>";
    table.rows.forEach((row) => {
      const isStart = row.state === start_state;
      const isFinal = final_states.includes(row.state);
      html += `<tr class="${isStart ? "tt-start" : ""} ${isFinal ? "tt-final" : ""}"><td class="state-cell">${row.state}</td>`;
      table.alphabet.forEach((sym) => { html += `<td>${row.cells[sym]}</td>`; });
      html += "</tr>";
    });
    html += "</tbody></table>";
    tableContainer.innerHTML = html;

    verdictBox.innerHTML = `<span class="verdict ${result.accepted ? "accepted" : "rejected"}">${result.accepted ? "Accepted" : "Rejected"}</span>`;

    const frames = (result.snapshots.length ? result.snapshots : [[]]).map((active, i) => ({ active, logIndex: i - 1 }));

    const logLines = (result.log || []).map((entry, i) => {
      if (entry.stage === "start + \u03b5-closure") {
        return `<div data-line="${i}">Start + \u03b5-closure: {${entry.active.join(", ")}}</div>`;
      }
      return `<div data-line="${i}">Step ${i}: consume "${entry.symbol}" \u2192 {${entry.moved_to.join(", ") || "&empty;"}} \u2192 \u03b5-closure {${entry.active.join(", ") || "&empty;"}}</div>`;
    });
    if (logLines.length === 0) logLines.push('<div>The input has a symbol outside this pattern\'s alphabet, so it\'s rejected immediately.</div>');
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

  form.requestSubmit();
})();
