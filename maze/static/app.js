const gridEl = document.getElementById("grid");
const seedEl = document.getElementById("seed-value");
const distanceEl = document.getElementById("distance-value");
const movesEl = document.getElementById("moves-value");
const goalEl = document.getElementById("goal-value");
const stateJsonEl = document.getElementById("state-json");
const seedInput = document.getElementById("seed-input");
const statusEl = document.getElementById("status");

let state = null;

async function fetchState() {
  const res = await fetch("/api/state");
  state = await res.json();
  render();
}

async function newGame(seed) {
  const q = seed ? `?seed=${encodeURIComponent(seed)}` : "";
  const res = await fetch(`/api/new${q}`);
  state = await res.json();
  render();
}

async function move(dir) {
  const res = await fetch(`/api/move?dir=${dir}`);
  state = await res.json();
  render();
}

function render() {
  if (!state) return;
  seedEl.textContent = state.seed ?? "n/a";
  distanceEl.textContent = state.distance_traveled ?? 0;
  movesEl.textContent = state.moves ?? 0;
  goalEl.textContent = `${state.goal?.x ?? 0},${state.goal?.y ?? 0}`;
  statusEl.textContent =
    state.agent &&
    state.goal &&
    state.agent.x === state.goal.x &&
    state.agent.y === state.goal.y
      ? "Goal reached!"
      : "";

  renderGrid();
  stateJsonEl.textContent = JSON.stringify(state, null, 2);
}

function renderGrid() {
  gridEl.innerHTML = "";
  if (!state || !state.grid) return;
  state.grid.forEach((row, y) => {
    row.split("").forEach((cell, x) => {
      const el = document.createElement("div");
      el.classList.add("cell");
      if (cell === "#") el.classList.add("wall");
      if (state.start && x === state.start.x && y === state.start.y) {
        el.classList.add("start");
        el.textContent = "S";
      }
      if (state.goal && x === state.goal.x && y === state.goal.y) {
        el.classList.add("goal");
        el.textContent = "G";
      }
      if (state.agent && x === state.agent.x && y === state.agent.y) {
        el.classList.add("agent");
        el.textContent = "A";
      }
      gridEl.appendChild(el);
    });
  });
}

function bindControls() {
  document.getElementById("apply-seed").addEventListener("click", () => {
    const val = seedInput.value.trim();
    newGame(val || undefined);
  });

  document.getElementById("random-seed").addEventListener("click", () => {
    seedInput.value = "";
    newGame();
  });

  document.querySelectorAll("[data-move]").forEach((btn) => {
    btn.addEventListener("click", () => move(btn.dataset.move));
  });

  window.addEventListener("keydown", (e) => {
    const keyMap = {
      ArrowUp: "up",
      ArrowDown: "down",
      ArrowLeft: "left",
      ArrowRight: "right",
      w: "up",
      s: "down",
      a: "left",
      d: "right",
    };
    const dir = keyMap[e.key];
    if (dir) {
      e.preventDefault();
      move(dir);
    }
  });
}

bindControls();
fetchState();
