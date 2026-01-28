"""AlphaZero-lite training loop for Goro Goro.

Usage (local):
  python -m ai.train
"""

from __future__ import annotations

import os
from typing import List, Tuple

import numpy as np
import torch
import torch.nn.functional as F

from .config import Config
from .game import GameState
from .model import PolicyValueNet
from .replay_buffer import ReplayBuffer
from .self_play import play_game


def run_self_play(config: Config, model: PolicyValueNet, buffer: ReplayBuffer):
    for _ in range(config.games_per_iteration):
        samples = play_game(config, model)
        buffer.add_game(samples)


def train_model(config: Config, model: PolicyValueNet, buffer: ReplayBuffer):
    if len(buffer) == 0:
        return

    optimizer = torch.optim.Adam(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )

    model.train()
    for _ in range(config.epochs):
        batch = buffer.sample(config.batch_size)
        states, target_policies, target_values = zip(*batch)

        states = torch.from_numpy(np.stack(states)).float()
        target_policies = torch.from_numpy(np.stack(target_policies)).float()
        target_values = torch.tensor(target_values, dtype=torch.float32).unsqueeze(1)

        logits, values = model(states)
        policy_loss = -(target_policies * F.log_softmax(logits, dim=1)).sum(dim=1).mean()
        value_loss = F.mse_loss(values, target_values)
        loss = policy_loss + value_loss

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()


def save_checkpoint(config: Config, model: PolicyValueNet, iteration: int):
    os.makedirs(config.checkpoint_dir, exist_ok=True)
    path = os.path.join(config.checkpoint_dir, f"model_iter_{iteration}.pt")
    torch.save(model.state_dict(), path)


def main():
    config = Config()
    model = PolicyValueNet(action_size=config.action_size)
    buffer = ReplayBuffer()

    # Minimal loop: self-play -> train -> checkpoint.
    for iteration in range(1, 6):
        run_self_play(config, model, buffer)
        train_model(config, model, buffer)
        save_checkpoint(config, model, iteration)
        print(f"Iteration {iteration} complete. Buffer size: {len(buffer)}")


if __name__ == "__main__":
    main()
