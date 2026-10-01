// ---------------------------------------------------------------------------
// dashboard.js
// Handles two small pieces of behaviour on the home page:
//   1. Toggling the mobile navigation menu.
//   2. Animating the hero "live preview" automaton so the highlight loops
//      around the states, giving a taste of what every simulator does.
// ---------------------------------------------------------------------------

(function setupNavToggle() {
  const toggle = document.getElementById("navToggle");
  const links = document.querySelector(".nav-links");
  if (!toggle || !links) return;

  toggle.addEventListener("click", () => {
    const isOpen = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
})();

(function animateHeroAutomaton() {
  const svg = document.getElementById("heroAutomaton");
  if (!svg) return;

  const stateCount = 5;
  const stepDurationMs = 900;
  let current = 0;

  function highlight(index) {
    for (let i = 0; i < stateCount; i++) {
      const state = document.getElementById("state-" + i);
      const edge = document.getElementById("edge-" + i);
      if (state) state.classList.toggle("active", i === index);
      if (edge) edge.classList.toggle("active", i === index);
    }
  }

  highlight(current);
  setInterval(() => {
    current = (current + 1) % stateCount;
    highlight(current);
  }, stepDurationMs);
})();
