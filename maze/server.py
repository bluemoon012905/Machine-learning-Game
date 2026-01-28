#!/usr/bin/env python3
"""Minimal maze game server with a browser UI."""

from __future__ import annotations

import json
import random
import secrets
from collections import deque
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import parse_qs, urlparse

ROOT_DIR = Path(__file__).parent
STATIC_DIR = ROOT_DIR / "static"
SIZE = 10

_state: Dict[str, object] = {}


def _has_path(grid: List[str]) -> bool:
    """Check if a path exists between start and goal on the current grid."""
    start = (0, 0)
    goal = (SIZE - 1, SIZE - 1)
    q: deque[Tuple[int, int]] = deque([start])
    visited = {start}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            return True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < SIZE and 0 <= ny < SIZE and grid[ny][nx] != "#" and (nx, ny) not in visited:
                visited.add((nx, ny))
                q.append((nx, ny))
    return False


def _generate_grid(seed: int) -> List[str]:
    """Create a seeded, reproducible 10x10 maze that keeps start/goal open."""
    rng = random.Random(seed)
    wall_prob = 0.28
    for _ in range(10_000):
        grid: List[str] = []
        for y in range(SIZE):
            row: List[str] = []
            for x in range(SIZE):
                if (x, y) in ((0, 0), (SIZE - 1, SIZE - 1)):
                    row.append(".")
                else:
                    row.append("#" if rng.random() < wall_prob else ".")
            grid.append("".join(row))
        if _has_path(grid):
            return grid
        wall_prob = min(0.45, wall_prob + 0.02)
    # Fallback: return an empty grid if we somehow failed to generate a valid one.
    return ["." * SIZE for _ in range(SIZE)]


def _current_state() -> Dict[str, object]:
    return {
        "size": SIZE,
        "grid": _state.get("grid", []),
        "start": _state.get("start"),
        "goal": _state.get("goal"),
        "agent": _state.get("agent"),
        "distance_traveled": _state.get("distance_traveled", 0),
        "moves": _state.get("moves", 0),
        "seed": _state.get("seed"),
    }


def _reset(seed: int | None = None) -> Dict[str, object]:
    chosen_seed = seed if seed is not None else secrets.randbelow(2**31)
    grid = _generate_grid(chosen_seed)
    _state.update(
        {
            "seed": chosen_seed,
            "grid": grid,
            "start": {"x": 0, "y": 0},
            "goal": {"x": SIZE - 1, "y": SIZE - 1},
            "agent": {"x": 0, "y": 0},
            "distance_traveled": 0,
            "moves": 0,
        }
    )
    return _current_state()


def _move(direction: str) -> Dict[str, object]:
    dir_map = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    delta = dir_map.get(direction.lower())
    if not delta:
        return _current_state()

    dx, dy = delta
    agent = _state["agent"]
    nx, ny = agent["x"] + dx, agent["y"] + dy
    grid: List[str] = _state["grid"]  # type: ignore[assignment]

    if 0 <= nx < SIZE and 0 <= ny < SIZE and grid[ny][nx] != "#":
        agent = {"x": nx, "y": ny}
        _state["agent"] = agent
        _state["distance_traveled"] = int(_state.get("distance_traveled", 0)) + 1
    _state["moves"] = int(_state.get("moves", 0)) + 1
    return _current_state()


class MazeHandler(SimpleHTTPRequestHandler):
    """Serve the API and the static frontend."""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self._handle_api(parsed)
            return

        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def _handle_api(self, parsed) -> None:
        qs = parse_qs(parsed.query)
        path = parsed.path
        if path == "/api/state":
            self._respond_json(_current_state())
            return
        if path == "/api/new":
            seed_param = qs.get("seed", [None])[0]
            seed_value = None
            if seed_param:
                try:
                    seed_value = int(seed_param, 0)
                except ValueError:
                    seed_value = abs(hash(seed_param)) % (2**31)
            self._respond_json(_reset(seed_value))
            return
        if path == "/api/move":
            direction = qs.get("dir", [""])[0]
            self._respond_json(_move(direction))
            return
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b'{"error":"not found"}')

    def _respond_json(self, payload: Dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    _reset()
    handler = partial(MazeHandler, directory=str(STATIC_DIR))
    server = HTTPServer(("0.0.0.0", 8000), handler)
    print("Serving maze game on http://localhost:8000")
    print("API endpoints: /api/state, /api/new?seed=<seed>, /api/move?dir=up|down|left|right")
    server.serve_forever()


if __name__ == "__main__":
    main()
