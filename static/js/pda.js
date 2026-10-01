// ---------------------------------------------------------------------------
// pda.js — PDA Simulator
// Talks to POST /api/pda/run (modules/pda.py searches for an accepting run).
// ---------------------------------------------------------------------------

(function () {
  const form = document.getElementById("pdaForm");
  if (!form) return;

  const statesInput = document.getElementById("states");
  const inputAlphabetInput = document.getElementById("inputAlphabet");
  const stackAlphabetInput = document.getElementById("stackAlphabet");
  const startInput = document.getElementById("startState");
  const initialStackInput = document.getElementById("initialStackSymbol");
  const finalInput = document.getElementById("finalStates");
  const inputStringInput = document.getElementById("inputString");
  const errorBox = document.getElementById("formError");
  const resultsBox = document.getElementById("results");
  const stackDisplay = document.getElementById("stackDisplay");
  const tableContainer = document.getElementById("tableContainer");
  const simLog = document.getElementById("simLog");
  const verdictBox = document.getElementById("verdict");
  const stepCounter = document.getElementById("stepCounter");
  const remainingInputBox = document.getElementById("remainingInput");

  const editor = TOCViz.createRowEditor(
    document.getElementById("transitionsEditor"),
    [
      { key: "from", label: "From", placeholder: "q0" },
      { key: "symbol", label: "Symbol", placeholder: "a / eps" },
      { key: "pop", label: "Pop (top)", placeholder: "Z" },
      { key: "to", label: "To", placeholder: "q0" },
      { key: "push", label: "Push", placeholder: "AZ / eps" },
    ],
    []
  );

  let controller = null;

  function loadExample(ex) {
    statesInput.value = ex.states;
    inputAlphabetInput.value = ex.input_alphabet;
    stackAlphabetInput.value = ex.stack_alphabet;
    startInput.value = ex.start_state;
    initialStackInput.value = ex.initial_stack_symbol;
    finalInput.value = ex.final_states;
    inputStringInput.value = ex.sample_input;
    editor.setRows(ex.transitions);
  }

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const ex = window.PDA_EXAMPLES[parseInt(chip.dataset.example, 10)];
      loadExample(ex);
      form.requestSubmit();
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.textContent = "";

    const payload = {
      states: statesInput.value,
      input_alphabet: inputAlphabetInput.value,
      stack_alphabet: stackAlphabetInput.value,
      start_state: startInput.value,
      initial_stack_symbol: initialStackInput.value,
      final_states: finalInput.value,
      input_string: inputStringInput.value,
      transitions: editor.getRows(),
    };

    try {
      const response = await fetch("/api/pda/run", {
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
      renderRun(data.rows, data.result, initialStackInput.value.trim());
    } catch (err) {
      errorBox.textContent = "Couldn't reach the server. Please try again.";
    }
  });

  function renderRun(rows, result, initialStackSymbol) {
    resultsBox.hidden = false;

    let html = '<table class="transition-table"><thead><tr><th>From</th><th>Symbol</th><th>Pop</th><th>To</th><th>Push</th></tr></thead><tbody>';
    rows.forEach((r) => {
      html += `<tr><td>${r.from}</td><td>${r.symbol}</td><td>${r.pop}</td><td>${r.to}</td><td>${r.push}</td></tr>`;
    });
    html += "</tbody></table>";
    tableContainer.innerHTML = html;

    verdictBox.innerHTML = `<span class="verdict ${result.accepted ? "accepted" : "rejected"}">${result.accepted ? "Accepted" : "Rejected"}</span>`;

    if (!result.accepted) {
      stackDisplay.innerHTML = TOCViz.renderStack([]);
      simLog.innerHTML = "<div>No accepting run was found for this input.</div>";
      stepCounter.textContent = "";
      remainingInputBox.textContent = "";
      if (controller) controller.pause();
      return;
    }

    // Frame 0: initial stack, before any transition
    const frames = [{
      stack: [initialStackSymbol],
      remaining: result.input_string,
      logIndex: -1,
    }];
    result.trace.forEach((step, i) => {
      frames.push({ stack: step.stack_after, remaining: step.remaining_input, logIndex: i });
    });

    const logLines = result.trace.map((step, i) =>
      `<div data-line="${i}">Step ${i + 1}: ${step.from_state} --${step.symbol}--&gt; ${step.to_state}  (pop ${step.popped}, push ${step.pushed})</div>`
    );
    if (logLines.length === 0) logLines.push("<div>Accepted with no transitions needed.</div>");
    simLog.innerHTML = logLines.join("");

    function onShow(frame, index) {
      stackDisplay.innerHTML = TOCViz.renderStack(frame.stack);
      remainingInputBox.textContent = "Remaining input: " + (frame.remaining || "(none)");
      simLog.querySelectorAll("div").forEach((el) => el.classList.remove("current-line"));
      if (frame.logIndex >= 0) {
        const line = simLog.querySelector(`[data-line="${frame.logIndex}"]`);
        if (line) { line.classList.add("current-line"); line.scrollIntoView({ block: "nearest" }); }
      }
      stepCounter.textContent = `Step ${index} / ${frames.length - 1}`;
    }

    if (controller) controller.pause();
    controller = TOCViz.createStepController(frames, onShow, { intervalMs: 800 });
  }

  document.getElementById("btnStep").addEventListener("click", () => controller && controller.step());
  document.getElementById("btnRun").addEventListener("click", () => controller && controller.run());
  document.getElementById("btnPause").addEventListener("click", () => controller && controller.pause());
  document.getElementById("btnReset").addEventListener("click", () => controller && controller.reset());

  if (window.PDA_EXAMPLES && window.PDA_EXAMPLES.length) {
    loadExample(window.PDA_EXAMPLES[0]);
    form.requestSubmit();
  }
})();
