"""Simple replay buffer for self-play data."""

from collections import deque
from typing import Deque, List, Tuple


class ReplayBuffer:
    def __init__(self, max_size: int = 100000):
        self._buffer: Deque[Tuple] = deque(maxlen=max_size)

    def add_game(self, samples: List[Tuple]):
        self._buffer.extend(samples)

    def sample(self, batch_size: int):
        import random

        batch_size = min(batch_size, len(self._buffer))
        return random.sample(self._buffer, batch_size)

    def __len__(self):
        return len(self._buffer)
