"""Self-play data generation for AlphaZero-lite."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import random

from .game import GameState
from .mcts import MCTS


def play_game(config, model) -> List[Tuple]:
    """Runs one self-play game and returns training samples.

    Each sample: (state_planes, policy, value)
    value is from the perspective of the player to move at that state.
    """
    state = GameState.initial()
    mcts = MCTS(config)
    history = []

    while True:
        outcome = state.outcome()
        if outcome is not None:
            break
        if state.move_number > config.max_moves:
            outcome = 0
            break

        policy = mcts.search(state, model)
        temp = 1.0 if state.move_number <= config.temperature_moves else 0.0
        action = select_action(policy, temp)
        if action is None:
            # Fallback: no policy data, pick a legal move uniformly.
            legal_moves = state.generate_legal_moves()
            action = GameState.move_to_action(random.choice(legal_moves))

        history.append((state.to_planes(), policy, state.turn))
        state = state.apply_move(GameState.action_to_move(action))

    samples = []
    for planes, policy, player in history:
        value = outcome if player == "S" else -outcome
        samples.append((np.array(planes, dtype=np.float32), policy, float(value)))
    return samples


def select_action(policy: np.ndarray, temperature: float) -> int:
    if policy.sum() <= 0:
        return None
    if temperature == 0:
        return int(np.argmax(policy))
    policy = policy ** (1.0 / temperature)
    policy = policy / policy.sum()
    return int(np.random.choice(len(policy), p=policy))
