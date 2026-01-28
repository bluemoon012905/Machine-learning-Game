"""Monte Carlo Tree Search with policy/value guidance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np
import torch

from .game import GameState


@dataclass
class Node:
    prior: float
    visit_count: int = 0
    value_sum: float = 0.0
    children: Dict[int, "Node"] = field(default_factory=dict)

    def expanded(self) -> bool:
        return len(self.children) > 0

    def value(self) -> float:
        return self.value_sum / self.visit_count if self.visit_count > 0 else 0.0


class MCTS:
    def __init__(self, config):
        self.config = config

    def search(self, state: GameState, model) -> np.ndarray:
        root = Node(prior=0.0)
        policy, value = self._evaluate(state, model, add_noise=True)
        root.children = {a: Node(prior=p) for a, p in policy}

        for _ in range(self.config.num_simulations):
            node = root
            scratch = state
            search_path = [node]

            while node.expanded():
                action, node = self._select_child(node)
                scratch = scratch.apply_move(GameState.action_to_move(action))
                search_path.append(node)

            outcome = scratch.outcome()
            if outcome is None:
                policy, value = self._evaluate(scratch, model)
                node.children = {a: Node(prior=p) for a, p in policy}
            else:
                # Convert outcome to the perspective of the current player at this node.
                value = outcome if scratch.turn == "S" else -outcome

            self._backpropagate(search_path, value)

        return self._build_policy(root)

    def _select_child(self, node: Node) -> Tuple[int, Node]:
        best_score = -1e9
        best_action = None
        best_child = None
        sqrt_total = np.sqrt(node.visit_count + 1)

        for action, child in node.children.items():
            q = child.value()
            u = self.config.c_puct * child.prior * sqrt_total / (1 + child.visit_count)
            score = q + u
            if score > best_score:
                best_score = score
                best_action = action
                best_child = child

        return best_action, best_child

    def _evaluate(self, state: GameState, model, add_noise: bool = False):
        legal_moves = state.generate_legal_moves()
        legal_actions = [GameState.move_to_action(m) for m in legal_moves]
        legal_set = set(legal_actions)

        planes = np.array(state.to_planes(), dtype=np.float32)
        planes = torch.from_numpy(planes).unsqueeze(0)  # (1, 13, 6, 5)

        with torch.no_grad():
            policy_logits, value = model(planes)
            policy_logits = policy_logits.squeeze(0).cpu().numpy()
            value = float(value.item())

        # Mask invalid moves and normalize.
        mask = np.full(policy_logits.shape, -1e9, dtype=np.float32)
        mask[list(legal_set)] = 0.0
        policy_logits = policy_logits + mask
        policy = softmax(policy_logits)

        if add_noise:
            noise = np.random.dirichlet([self.config.dirichlet_alpha] * len(legal_actions))
            for idx, action in enumerate(legal_actions):
                policy[action] = (1 - self.config.root_noise_frac) * policy[action] + self.config.root_noise_frac * noise[idx]

        action_priors = [(a, float(policy[a])) for a in legal_actions]
        return action_priors, value

    @staticmethod
    def _backpropagate(path: List[Node], value: float):
        for node in reversed(path):
            node.value_sum += value
            node.visit_count += 1
            value = -value

    @staticmethod
    def _build_policy(root: Node) -> np.ndarray:
        policy = np.zeros(GameState.action_size(), dtype=np.float32)
        if root.visit_count == 0:
            return policy
        for action, child in root.children.items():
            policy[action] = child.visit_count
        policy = policy / np.sum(policy)
        return policy


def softmax(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x)
    exp = np.exp(x)
    return exp / np.sum(exp)
