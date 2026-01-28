"""Training and model configuration for Goro Goro AlphaZero-lite."""

from dataclasses import dataclass


@dataclass
class Config:
    # Board / rules
    rows: int = 6
    cols: int = 5

    # Action space
    action_size: int = 30 * 30 * 2 + 3 * 30  # move (from,to,promo) + drop (piece,to)

    # MCTS
    num_simulations: int = 200
    c_puct: float = 1.4
    dirichlet_alpha: float = 0.3
    root_noise_frac: float = 0.25

    # Self-play
    games_per_iteration: int = 24
    max_moves: int = 240
    temperature_moves: int = 20

    # Training
    batch_size: int = 128
    epochs: int = 2
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4

    # Checkpoints
    checkpoint_dir: str = "checkpoints"
    export_policy_file: str = "policy_latest.json"
