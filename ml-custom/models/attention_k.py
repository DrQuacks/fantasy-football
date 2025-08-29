from .attention_base import PositionAttentionModel
from .targets import K_TARGETS

class KModel(PositionAttentionModel):
    def __init__(self, F_player, F_defense, num_teammates=2, d=64, heads=2):
        super().__init__(
            F_player=F_player,
            F_defense=F_defense,
            num_teammates=num_teammates,  # for K: QB1 + RB1 only
            targets=K_TARGETS,
            d=d,
            num_heads=heads,
        )
