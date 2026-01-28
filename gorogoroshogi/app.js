const ROWS = 6;
const COLS = 5;
const PLAYER_S = "S";
const PLAYER_N = "N";

const PIECE_NAMES = {
  L: "Lion",
  D: "Dog",
  C: "Cat",
  P: "Chick",
  H: "Hen",
  U: "Super Cat",
};

const PIECE_CLASS = {
  L: "lion",
  D: "dog",
  C: "cat",
  P: "chick",
  H: "hen",
  U: "supercat",
};

const PROMOTES = {
  P: "H",
  C: "U",
};

const DEMOTES = {
  H: "P",
  U: "C",
};

const BACK_RANK = ["C", "D", "L", "D", "C"];
const PAWN_COLS = [1, 2, 3];
const PAWN_ROWS = { N: 2, S: 3 };

const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const handNEl = document.getElementById("hand-n");
const handSEl = document.getElementById("hand-s");
const resetBtn = document.getElementById("reset");
const exportBtn = document.getElementById("export");
const toggleLegalBtn = document.getElementById("toggle-legal");

const promoModal = document.getElementById("promotion-modal");
const promoYes = document.getElementById("promote-yes");
const promoNo = document.getElementById("promote-no");

const exportModal = document.getElementById("export-modal");
const exportText = document.getElementById("export-text");
const exportCopy = document.getElementById("export-copy");
const exportClose = document.getElementById("export-close");

let state = initialState();
let selected = null;
let pendingPromotion = null;
let showLegal = true;

function initialState() {
  const board = Array.from({ length: ROWS }, () => Array(COLS).fill(null));
  BACK_RANK.forEach((type, c) => {
    board[0][c] = { type, owner: PLAYER_N };
    board[ROWS - 1][c] = { type, owner: PLAYER_S };
  });
  PAWN_COLS.forEach((c) => {
    board[PAWN_ROWS.N][c] = { type: "P", owner: PLAYER_N };
    board[PAWN_ROWS.S][c] = { type: "P", owner: PLAYER_S };
  });

  return {
    board,
    hands: {
      [PLAYER_N]: { P: 0, C: 0, D: 0 },
      [PLAYER_S]: { P: 0, C: 0, D: 0 },
    },
    turn: PLAYER_S,
    moveNumber: 1,
    winner: null,
  };
}

function cloneState(src) {
  return {
    board: src.board.map((row) =>
      row.map((cell) => (cell ? { ...cell } : null))
    ),
    hands: {
      [PLAYER_N]: { ...src.hands[PLAYER_N] },
      [PLAYER_S]: { ...src.hands[PLAYER_S] },
    },
    turn: src.turn,
    moveNumber: src.moveNumber,
    winner: src.winner,
  };
}

function inBounds(r, c) {
  return r >= 0 && r < ROWS && c >= 0 && c < COLS;
}

function forwardDir(player) {
  return player === PLAYER_S ? -1 : 1;
}

function enemyCamp(player, row) {
  if (player === PLAYER_S) {
    return row === 0 || row === 1;
  }
  return row === ROWS - 1 || row === ROWS - 2;
}

function lastRank(player, row) {
  return player === PLAYER_S ? row === 0 : row === ROWS - 1;
}

function movementDeltas(type, player) {
  const f = forwardDir(player);
  switch (type) {
    case "L":
      return [
        [-1, -1],
        [-1, 0],
        [-1, 1],
        [0, -1],
        [0, 1],
        [1, -1],
        [1, 0],
        [1, 1],
      ];
    case "D":
    case "H":
    case "U":
      return [
        [f, 0],
        [f, -1],
        [f, 1],
        [0, -1],
        [0, 1],
        [-f, 0],
      ];
    case "C":
      return [
        [f, 0],
        [f, -1],
        [f, 1],
        [-f, -1],
        [-f, 1],
      ];
    case "P":
      return [[f, 0]];
    default:
      return [];
  }
}

function generatePseudoMoves(stateObj, r, c, piece) {
  const deltas = movementDeltas(piece.type, piece.owner);
  const moves = [];
  deltas.forEach(([dr, dc]) => {
    const nr = r + dr;
    const nc = c + dc;
    if (!inBounds(nr, nc)) return;
    const target = stateObj.board[nr][nc];
    if (target && target.owner === piece.owner) return;
    moves.push({
      from: { r, c },
      to: { r: nr, c: nc },
      piece: piece.type,
      promote: false,
      drop: false,
    });
  });
  return moves;
}

function applyPromotionOptions(pieceType, from, to, player, move) {
  if (!PROMOTES[pieceType]) return [move];
  const inCamp = enemyCamp(player, from.r) || enemyCamp(player, to.r);
  if (!inCamp) return [move];

  const mustPromote = pieceType === "P" && lastRank(player, to.r);
  if (mustPromote) {
    return [{ ...move, promote: true }];
  }

  return [
    { ...move, promote: false },
    { ...move, promote: true },
  ];
}

function generateMovesForPiece(stateObj, r, c, piece) {
  const baseMoves = generatePseudoMoves(stateObj, r, c, piece);
  const withPromotion = [];
  baseMoves.forEach((move) => {
    const options = applyPromotionOptions(
      piece.type,
      move.from,
      move.to,
      piece.owner,
      move
    );
    withPromotion.push(...options);
  });
  return withPromotion;
}

function hasPawnInFile(stateObj, player, file) {
  for (let r = 0; r < ROWS; r += 1) {
    const cell = stateObj.board[r][file];
    if (cell && cell.owner === player && cell.type === "P") {
      return true;
    }
  }
  return false;
}

function isPawnDropMate(stateObj, player, r, c) {
  const move = { drop: true, piece: "P", to: { r, c } };
  const next = applyMove(stateObj, move);
  const opponent = player === PLAYER_S ? PLAYER_N : PLAYER_S;
  if (!isInCheck(next, opponent)) return false;
  const oppMoves = generateLegalMoves(next, opponent, {
    skipPawnDropMateCheck: true,
  });
  return oppMoves.length === 0;
}

function generateDropMoves(stateObj, player, options = {}) {
  const moves = [];
  const hand = stateObj.hands[player];
  const skipPawnDropMateCheck = options.skipPawnDropMateCheck === true;
  Object.keys(hand).forEach((pieceType) => {
    if (hand[pieceType] <= 0) return;
    for (let r = 0; r < ROWS; r += 1) {
      for (let c = 0; c < COLS; c += 1) {
        if (stateObj.board[r][c]) continue;
        if (pieceType === "P") {
          if (lastRank(player, r)) continue;
          if (hasPawnInFile(stateObj, player, c)) continue;
          if (!skipPawnDropMateCheck && isPawnDropMate(stateObj, player, r, c)) {
            continue;
          }
        }
        moves.push({
          drop: true,
          piece: pieceType,
          to: { r, c },
        });
      }
    }
  });
  return moves;
}

function findLion(stateObj, player) {
  for (let r = 0; r < ROWS; r += 1) {
    for (let c = 0; c < COLS; c += 1) {
      const cell = stateObj.board[r][c];
      if (cell && cell.owner === player && cell.type === "L") {
        return { r, c };
      }
    }
  }
  return null;
}

function isInCheck(stateObj, player) {
  const lionPos = findLion(stateObj, player);
  if (!lionPos) return true;
  const opponent = player === PLAYER_S ? PLAYER_N : PLAYER_S;
  for (let r = 0; r < ROWS; r += 1) {
    for (let c = 0; c < COLS; c += 1) {
      const piece = stateObj.board[r][c];
      if (!piece || piece.owner !== opponent) continue;
      const deltas = movementDeltas(piece.type, piece.owner);
      for (const [dr, dc] of deltas) {
        const nr = r + dr;
        const nc = c + dc;
        if (nr === lionPos.r && nc === lionPos.c) {
          return true;
        }
      }
    }
  }
  return false;
}

function applyMove(stateObj, move) {
  const next = cloneState(stateObj);
  const player = next.turn;

  if (move.drop) {
    next.board[move.to.r][move.to.c] = { type: move.piece, owner: player };
    next.hands[player][move.piece] -= 1;
  } else {
    const piece = next.board[move.from.r][move.from.c];
    const target = next.board[move.to.r][move.to.c];
    next.board[move.from.r][move.from.c] = null;

    if (target) {
      const capturedType = DEMOTES[target.type] || target.type;
      if (capturedType !== "L") {
        next.hands[player][capturedType] += 1;
      }
    }

    let newType = piece.type;
    if (move.promote && PROMOTES[piece.type]) {
      newType = PROMOTES[piece.type];
    }

    next.board[move.to.r][move.to.c] = {
      type: newType,
      owner: player,
    };
  }

  const opponent = player === PLAYER_S ? PLAYER_N : PLAYER_S;
  const opponentLion = findLion(next, opponent);
  if (!opponentLion) {
    next.winner = player;
  }

  next.turn = opponent;
  next.moveNumber += 1;

  if (!next.winner) {
    const oppMoves = generateLegalMoves(next, opponent);
    if (oppMoves.length === 0) {
      next.winner = isInCheck(next, opponent) ? player : "Draw";
    }
  }

  return next;
}

function generateLegalMoves(stateObj, player, options = {}) {
  const moves = [];
  for (let r = 0; r < ROWS; r += 1) {
    for (let c = 0; c < COLS; c += 1) {
      const piece = stateObj.board[r][c];
      if (!piece || piece.owner !== player) continue;
      const candidateMoves = generateMovesForPiece(stateObj, r, c, piece);
      candidateMoves.forEach((move) => moves.push(move));
    }
  }

  generateDropMoves(stateObj, player, options).forEach((move) => moves.push(move));

  return moves.filter((move) => {
    const next = applyMove(stateObj, move);
    return !isInCheck(next, player);
  });
}

function serializeState(stateObj) {
  return {
    board: stateObj.board.map((row) =>
      row.map((cell) => (cell ? { ...cell } : null))
    ),
    hands: {
      N: { ...stateObj.hands[PLAYER_N] },
      S: { ...stateObj.hands[PLAYER_S] },
    },
    turn: stateObj.turn,
    moveNumber: stateObj.moveNumber,
    winner: stateObj.winner,
  };
}

function encodeForAI(stateObj) {
  const types = ["L", "D", "C", "P", "H", "U"];
  const planes = Array.from({ length: types.length * 2 }, () =>
    Array.from({ length: ROWS }, () => Array(COLS).fill(0))
  );

  for (let r = 0; r < ROWS; r += 1) {
    for (let c = 0; c < COLS; c += 1) {
      const cell = stateObj.board[r][c];
      if (!cell) continue;
      const typeIndex = types.indexOf(cell.type);
      if (typeIndex < 0) continue;
      const offset = cell.owner === PLAYER_S ? 0 : types.length;
      planes[typeIndex + offset][r][c] = 1;
    }
  }

  return {
    planes,
    hands: {
      N: { ...stateObj.hands[PLAYER_N] },
      S: { ...stateObj.hands[PLAYER_S] },
    },
    turn: stateObj.turn,
  };
}

function setSelected(nextSelected) {
  selected = nextSelected;
  render();
}

function renderStatus() {
  if (state.winner) {
    statusEl.textContent =
      state.winner === "Draw" ? "Draw" : `${labelPlayer(state.winner)} wins!`;
    return;
  }
  statusEl.textContent = `Turn ${state.moveNumber}: ${labelPlayer(state.turn)}`;
}

function labelPlayer(player) {
  return player === PLAYER_S ? "South" : "North";
}

function renderBoard() {
  boardEl.innerHTML = "";
  const legalMoves = selected ? getMovesForSelection() : [];

  for (let r = 0; r < ROWS; r += 1) {
    for (let c = 0; c < COLS; c += 1) {
      const square = document.createElement("div");
      square.className = "square";
      square.dataset.r = r;
      square.dataset.c = c;

      const piece = state.board[r][c];
      if (piece) {
        square.appendChild(buildToken(piece));
      }

      if (selected && selected.type === "board" && selected.r === r && selected.c === c) {
        square.classList.add("highlight");
      }

      if (showLegal) {
        legalMoves.forEach((move) => {
          if (move.to && move.to.r === r && move.to.c === c) {
            square.classList.add("legal");
            if (state.board[r][c]) square.classList.add("capture");
          }
        });
      }

      square.addEventListener("click", () => handleSquareClick(r, c));
      boardEl.appendChild(square);
    }
  }
}

function buildToken(piece) {
  const token = document.createElement("div");
  token.className = `token ${PIECE_CLASS[piece.type]} ${piece.owner === PLAYER_S ? "south" : "north"}`;

  const face = document.createElement("div");
  face.className = "face";
  const label = document.createElement("div");
  label.className = "label";
  label.textContent = PIECE_NAMES[piece.type];

  token.appendChild(face);
  token.appendChild(label);
  return token;
}

function renderHands() {
  handNEl.innerHTML = "";
  handSEl.innerHTML = "";

  renderHandSection(handNEl, PLAYER_N);
  renderHandSection(handSEl, PLAYER_S);
}

function renderHandSection(container, player) {
  const title = document.createElement("div");
  title.className = "hand-title";
  title.textContent = `${labelPlayer(player)} hand`;
  container.appendChild(title);

  ["P", "C", "D"].forEach((pieceType) => {
    const item = document.createElement("div");
    item.className = "hand-item";
    if (selected && selected.type === "hand" && selected.player === player && selected.piece === pieceType) {
      item.classList.add("active");
    }

    const token = buildToken({ type: pieceType, owner: player });
    token.style.pointerEvents = "none";

    const count = document.createElement("div");
    count.className = "count";
    count.textContent = `x${state.hands[player][pieceType]}`;

    item.appendChild(token);
    item.appendChild(count);
    item.addEventListener("click", () => handleHandClick(player, pieceType));
    container.appendChild(item);
  });
}

function handleHandClick(player, pieceType) {
  if (state.winner) return;
  if (player !== state.turn) return;
  if (state.hands[player][pieceType] <= 0) return;

  if (selected && selected.type === "hand" && selected.piece === pieceType) {
    setSelected(null);
    return;
  }

  setSelected({ type: "hand", player, piece: pieceType });
}

function handleSquareClick(r, c) {
  if (state.winner) return;

  const piece = state.board[r][c];

  if (!selected) {
    if (piece && piece.owner === state.turn) {
      setSelected({ type: "board", r, c });
    }
    return;
  }

  if (selected.type === "hand") {
    const moves = getMovesForSelection();
    const match = moves.find((move) => move.to.r === r && move.to.c === c);
    if (match) {
      state = applyMove(state, match);
      setSelected(null);
    }
    return;
  }

  if (selected.type === "board") {
    if (piece && piece.owner === state.turn) {
      setSelected({ type: "board", r, c });
      return;
    }

    const moves = getMovesForSelection();
    const matches = moves.filter((move) => move.to.r === r && move.to.c === c);
    if (matches.length === 0) return;

    if (matches.length === 1 && !matches[0].promote) {
      state = applyMove(state, matches[0]);
      setSelected(null);
      return;
    }

    if (matches.length === 1 && matches[0].promote) {
      state = applyMove(state, matches[0]);
      setSelected(null);
      return;
    }

    if (matches.length >= 2) {
      pendingPromotion = {
        promote: matches.find((m) => m.promote),
        stay: matches.find((m) => !m.promote),
      };
      openPromoModal();
    }
  }
}

function getMovesForSelection() {
  if (!selected) return [];
  const moves = generateLegalMoves(state, state.turn);

  if (selected.type === "board") {
    return moves.filter(
      (m) =>
        !m.drop &&
        m.from.r === selected.r &&
        m.from.c === selected.c
    );
  }

  return moves.filter((m) => m.drop && m.piece === selected.piece);
}

function openPromoModal() {
  promoModal.classList.remove("hidden");
}

function closePromoModal() {
  promoModal.classList.add("hidden");
  pendingPromotion = null;
}

function render() {
  renderStatus();
  renderBoard();
  renderHands();
}

promoYes.addEventListener("click", () => {
  if (pendingPromotion && pendingPromotion.promote) {
    state = applyMove(state, pendingPromotion.promote);
  }
  closePromoModal();
  setSelected(null);
});

promoNo.addEventListener("click", () => {
  if (pendingPromotion && pendingPromotion.stay) {
    state = applyMove(state, pendingPromotion.stay);
  }
  closePromoModal();
  setSelected(null);
});

resetBtn.addEventListener("click", () => {
  state = initialState();
  setSelected(null);
});

exportBtn.addEventListener("click", () => {
  exportText.value = JSON.stringify(serializeState(state), null, 2);
  exportModal.classList.remove("hidden");
});

exportCopy.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(exportText.value);
    exportCopy.textContent = "Copied!";
    setTimeout(() => (exportCopy.textContent = "Copy JSON"), 1200);
  } catch (err) {
    exportCopy.textContent = "Copy failed";
  }
});

exportClose.addEventListener("click", () => {
  exportModal.classList.add("hidden");
});

toggleLegalBtn.addEventListener("click", () => {
  showLegal = !showLegal;
  toggleLegalBtn.textContent = showLegal ? "Hide Legal Moves" : "Show Legal Moves";
  render();
});

toggleLegalBtn.textContent = "Hide Legal Moves";

window.GoroGoro = {
  initialState,
  generateLegalMoves,
  applyMove,
  serializeState,
  encodeForAI,
};

render();
