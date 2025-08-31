# ml-custom/config.py
from dataclasses import dataclass

@dataclass
class TrainConfig:
    # Optimizer
    lr: float = 3e-4
    weight_decay: float = 1e-4

    # Data / training loop
    batch_size: int = 32
    num_epochs: int = 10

    # Loss knobs
    huber_delta: float = 1.0

    # You can add more here as needed:
    # dropout: float = 0.10
    # clip_grad_norm: float | None = 1.0
    # seed: int = 42
