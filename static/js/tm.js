// ---------------------------------------------------------------------------
// tm.js — Turing Machine Simulator
// Talks to POST /api/tm/run (modules/turing_machine.py runs the machine).
// ---------------------------------------------------------------------------

(function () {
  const form = document.getElementById("tmForm");
  if (!form) return;

  const statesInput = document.getElementById("states");
  const tapeAlphabetInput = document.getElementById("tapeAlphabet");
  const inputAlphabetInput = document.getElementById("inputAlphabet");
  const blankInput = document.getElementById("blankSymbol");
  const startInput = document.getElementById("startState");
  const finalInput = document.getElementById("finalStates");
  const inputStringInput = document.getElementById("inputString");
  const errorBox = document.getElementById("formError");
  const resultsBox = document.getElementById("results");
  const tapeDisplay = document.getElementById("tapeDisplay");
  const tableContainer = document.getElementById("tableContainer");
  const simLog = document.getElementById("simLog");
  const verdictBox = document.getElementById("verdict");
  const stepCounter = document.getElementById("stepCounter");
  const stateInfo = document.getElementById("stateInfo");

  const editor = TOCViz.createRowEditor(
    document.getElementById("transitionsEditor"),
    [
      { key: "state", label: "State", placeholder: "q0" },
      { key: "read", label: "Read", placeholder: "0" },
      { key: "write", label: "Write", placeholder: "1" },
      { key: "move", label: "Move", placeholder: "R" },
      { key: "next_state", label: "Next state", placeholder: "q0" },
    ],
    []
  );

  let controller = null;

  function loadExample(ex) {
    statesInput.value = ex.states;
    tapeAlphabetInput.value = ex.tape_alphabet;
    inputAlphabetInput.value = ex.input_alphabet;
    blankInput.value = ex.blank_symbol;
    startInput.value = ex.start_state;
    finalInput.value = ex.final_states;
    inputStringInput.value = ex.sample_input;
    editor.setRows(ex.transitions);
  }

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const ex = window.TM_EXAMPLES[parseInt(chip.dataset.example, 10)];
      loadExample(ex);
      form.requestSubmit();
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.textContent = "";

    const payload = {
      states: statesInput.value,
      tape_alphabet: tapeAlphabetInput.value,
      input_alphabet: inputAlphabetInput.value,
      blank_symbol: blankInput.value,
      start_state: startInput.value,
      final_states: finalInput.value,
      input_string: inputStringInput.value,
      transitions: editor.getRows(),
    };

    try {
      const response = await fetch("/api/tm/run", {
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
      renderRun(data.rows, data.result);
    } catch (err) {
      errorBox.textContent = "Couldn't reach the server. Please try again.";
    }
  });

  function renderRun(rows, result) {
    resultsBox.hidden = false;

    let html = '<table class="transition-table"><thead><tr><th>State</th><th>Read</th><th>Write</th><th>Move</th><th>Next state</th></tr></thead><tbody>';
    rows.forEach((r) => {
      html += `<tr><td>${r.state}</td><td>${r.read}</td><td>${r.write}</td><td>${r.move}</td><td>${r.next_state}</td></tr>`;
    });
    html += "</tbody></table>";
    tableContainer.innerHTML = html;

    const statusText = result.accepted
      ? "Accepted"
      : (result.halted ? "Rejected (halted in a non-final state)" : "Rejected (did not halt within the step limit)");
    verdictBox.innerHTML = `<span class="verdict ${result.accepted ? "accepted" : "rejected"}">${statusText}</span>`;

    const frames = result.history;
    const logLines = frames.map((f, i) =>
      `<div data-line="${i}">Step ${f.step}: state ${f.state}, reading "${f.read}" at position ${f.head}</div>`
    );
    simLog.innerHTML = logLines.join("");

    function onShow(frame, index) {
      tapeDisplay.innerHTML = TOCViz.renderTape(frame.tape, frame.head);
      stateInfo.textContent = `Current state: ${frame.state}  |  Reading: "${frame.read}"  |  Head position: ${frame.head}`;
      simLog.querySelectorAll("div").forEach((el) => el.classList.remove("current-line"));
      const line = simLog.querySelector(`[data-line="${index}"]`);
      if (line) { line.classList.add("current-line"); line.scrollIntoView({ block: "nearest" }); }
      stepCounter.textContent = `Step ${index} / ${frames.length - 1}`;
    }

    if (controller) controller.pause();
    controller = TOCViz.createStepController(frames, onShow, { intervalMs: 500 });
  }

  document.getElementById("btnStep").addEventListener("click", () => controller && controller.step());
  document.getElementById("btnRun").addEventListener("click", () => controller && controller.run());
  document.getElementById("btnPause").addEventListener("click", () => controller && controller.pause());
  document.getElementById("btnReset").addEventListener("click", () => controller && controller.reset());

  if (window.TM_EXAMPLES && window.TM_EXAMPLES.length) {
    loadExample(window.TM_EXAMPLES[0]);
    form.requestSubmit();
  }
})();
