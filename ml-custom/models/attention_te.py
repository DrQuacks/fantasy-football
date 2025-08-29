from .attention_base import PositionAttentionModel
from .targets import TE_TARGETS

class TEModel(PositionAttentionModel):
    def __init__(self, F_player, F_defense, num_teammates=11, d=64, heads=4):
        super().__init__(
            F_player=F_player,
            F_defense=F_defense,
            num_teammates=num_teammates,
            targets=TE_TARGETS,
            d=d,
            num_heads=heads,
        )
