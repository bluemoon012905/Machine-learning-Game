# Machine Learning Game Arena

This repo hosts a collection of small competitive machine learning games. Players build and train agents against the game environments here, then compare scores to see whose model performs best. Each game lives in its own folder and comes with starter docs and baseline rules.

## What you can do
- Browse the available games and pick one to tackle.
- Train an agent locally or in your own infra; no server dependencies are assumed.
- Share results, tweaks, and improvements via issues or PRs.

## Games
- `maze/`: 10x10 maze maker/solver with full, AI-readable game state. Agents must navigate to a single goal block while tracking the seed and distance traveled.

## Run locally
- Requirements: Python 3.9+ (no external deps).
- Start the maze game: `python3 maze/server.py` then open `http://localhost:8000` in a browser.
- API endpoints for agents: `/api/state` (current state), `/api/new?seed=<seed>` (new maze with provided or random seed), `/api/move?dir=up|down|left|right` (step the agent).
- Quick check: `python3 -m py_compile maze/server.py` to verify the server script loads.

## Contributing
Game ideas, environment tweaks, and baseline agents are all welcome. Keep assets and code for each game scoped to its folder.
