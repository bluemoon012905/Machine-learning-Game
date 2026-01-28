# Maze Maker/Solver Game

## Goal
Create an agent that can solve procedurally generated mazes by reaching a single goal block on a fixed 10x10 grid. Variants can also include generating challenging mazes for opponents to solve using the same rules.

## Environment
- Fixed 10x10 grid with walls, empty cells, a single start, and a single goal block.
- Observations: full, AI-readable game state (grid layout, agent position, goal position, live stats).
- Actions: move up/down/left/right (no diagonal). Invalid moves keep the agent in place.
- Episode ends when the goal is reached or a move/time budget is exhausted.

## Scoring
- Primary: fewest steps to reach the goal within the budget.
- Secondary tiebreaker: time to compute each move (faster is better).
- Optional maker variant: score your generated maze by how long a baseline solver takes compared to a reference set.

## Live stats and seed handling
- Random seed drives maze generation; it can be user-specified or randomly generated.
- The seed and distance traveled are tracked live and exposed to players/agents alongside the grid state.

## Game state visibility
- All parts of the game state (grid, agent position, goal position, seed, distance traveled, remaining budget) are serializable/readable by an AI agent without hidden information.

## Running the reference server
- Requirements: Python 3.9+ (no extra packages).
- Start: `python3 server.py`, then open `http://localhost:8000` to see the browser UI.
- Controls: arrow keys/WASD or on-screen arrows. Enter a seed to recreate a maze; leave empty for a random seed.
- Optional check: `python3 -m py_compile server.py` to validate the script before running.

## API for agents
- `GET /api/state` → current game state JSON.
- `GET /api/new?seed=<seed>` → start a new maze with the provided seed; omit the seed for a random one.
- `GET /api/move?dir=up|down|left|right` → attempt a move; invalid moves leave the agent in place.
- State fields: `size`, `grid` (list of 10 strings), `start`, `goal`, `agent`, `distance_traveled`, `moves`, `seed`.

## Files
- This folder is for environment code, baselines, and assets specific to the maze game.

## Starter ideas
- Try BFS/A* for a fast, reliable solver baseline.
- Train a small RL policy (e.g., DQN or PPO) on random mazes.
- Use curriculum learning: start with small mazes, then scale up size and wall density.
