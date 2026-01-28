"""Policy + value network for AlphaZero-lite.

Lightweight conv stack suitable for 5x6 board.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class PolicyValueNet(nn.Module):
    def __init__(self, action_size: int, channels: int = 64):
        super().__init__()
        self.conv1 = nn.Conv2d(13, channels, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)

        self.policy_conv = nn.Conv2d(channels, 32, kernel_size=1)
        self.policy_fc = nn.Linear(32 * 6 * 5, action_size)

        self.value_conv = nn.Conv2d(channels, 16, kernel_size=1)
        self.value_fc1 = nn.Linear(16 * 6 * 5, 64)
        self.value_fc2 = nn.Linear(64, 1)

    def forward(self, x):
        # x shape: (batch, 13, 6, 5)
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))

        policy = F.relu(self.policy_conv(x))
        policy = policy.flatten(1)
        policy = self.policy_fc(policy)

        value = F.relu(self.value_conv(x))
        value = value.flatten(1)
        value = F.relu(self.value_fc1(value))
        value = torch.tanh(self.value_fc2(value))

        return policy, value
