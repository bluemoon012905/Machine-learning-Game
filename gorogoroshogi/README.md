# Goro Goro

A single-page, GitHub Pages-ready implementation of **Goro Goro Shogi** (mini shogi, 5x6) with a cute animal interface and an AI-friendly game state engine. The UI is built for human play now, and the internal engine is structured for self-play training later.

## What You Get
- 5x6 Goro Goro Shogi board with animal pieces
- Legal move generation, captures, drops, promotion
- Deterministic state model + JSON export
- Front-page-only web app (no build step)

## Assumed Rules (please confirm)
This implementation uses the common mini-shogi layout and movement set:

Board size
- 5 columns x 6 rows

Pieces per side
- Lion (King)
- 2 Dogs (Gold)
- 2 Cats (Silver)
- 3 Chicks (Pawns)

Starting setup (North at top, South at bottom)
- Back rank: Cat, Dog, Lion, Dog, Cat
- Middle ranks: three Chicks on files B, C, D for both sides (meet in the middle)

Promotion
- Chicks and Cats can promote in the enemy camp (last two ranks)
- A Chick that reaches the last rank must promote

Drops
- Captured pieces go to hand and may be dropped later
- A Chick may not be dropped on the last rank
- A Chick may not be dropped on a file that already contains an unpromoted Chick

Drop-mate (uchi-fuzume) is enforced.

If any of this differs from your preferred ruleset, tell me and I will adjust.

## Run Locally
Open `index.html` in a browser.

## AI Hooks
The engine exposes functions for training workflows:

- `window.GoroGoro.initialState()`
- `window.GoroGoro.generateLegalMoves(state, player)`
- `window.GoroGoro.applyMove(state, move)`
- `window.GoroGoro.serializeState(state)`
- `window.GoroGoro.encodeForAI(state)`

Use `Export State` in the UI to grab the current JSON snapshot. Later, a local training script can load or export a policy file that the page can consume.

## Files
- `index.html` – single page layout
- `styles.css` – bold, playful animal-themed visuals
- `app.js` – rules engine + UI bindings

## Next Milestones
- Confirm rules and starting setup
- Add AI policy loader (local JSON -> browser)
- Add self-play and evaluation harness (local)

## Local AI Training (AlphaZero-lite)

The `ai/` folder contains a commented, minimal AlphaZero-style training scaffold (self-play + MCTS + policy/value net).

Requirements (local):
- Python 3.10+
- PyTorch

Run (local):
- `python -m ai.train`

Outputs: model checkpoints in `ai/checkpoints/`. Exporting a browser-usable policy file will be added later.
