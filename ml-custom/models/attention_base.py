import torch, torch.nn as nn
from .common_blocks import MLP, BucketedCrossAttention

class PositionAttentionModel(nn.Module):
    """
    Generic: encodes player, teammates, defense; cross-attends player→teammates;
    optional temporal block; multitask heads defined by `targets`.
    """
    def __init__(self, F_player, F_defense, num_teammates, targets, d=64, num_heads=4):
        super().__init__()
        self.num_teammates = num_teammates
        self.targets = targets  # e.g., ["points","receivingYards","receivingTDs","receptions"]

        # Encoders
        self.player_enc = MLP(F_player, d_hidden=128, d_out=d)
        self.tm_enc     = MLP(F_player, d_hidden=128, d_out=d)    # shared across all teammate rows
        self.def_enc    = MLP(F_defense, d_hidden=128, d_out=d) if F_defense > 0 else nn.Identity()

        # Slot embeddings: fixed QB→RB→WR→TE order (or QB→RB for K); size = num_teammates
        self.slot_embed = nn.Embedding(num_teammates, d)

        # Cross-attention
        self.cross_attn = BucketedCrossAttention(d_model=d, num_heads=num_heads)

        # Trunk and heads
        self.trunk = MLP(d*3, d_hidden=256, d_out=2*d)  # player + team_repr + defense
        self.heads = nn.ModuleDict({name: nn.Linear(2*d, 1) for name in self.targets})

    def forward(self, batch):
        # Inputs
        p = batch["player_features"]            # (B, F_player)
        T = batch["teammate_features"]          # (B, N, F_player)
        d = batch["defense_features"]           # (B, F_defense) or (B,0)

        # Encode
        p_e = self.player_enc(p)                # (B, d)
        T_e = self.tm_enc(T)                    # (B, N, d)
        # add slot embeddings
        idx = torch.arange(self.num_teammates, device=T_e.device).unsqueeze(0)  # (1,N)
        T_e = T_e + self.slot_embed(idx)

        # Cross-attention player→team
        team_repr, attn = self.cross_attn(p_e, T_e)   # (B,d), (B,N)

        # Defense
        d_e = self.def_enc(d) if not isinstance(self.def_enc, nn.Identity) else d

        # Fuse
        x = torch.cat([p_e, team_repr, d_e], dim=1)   # (B, 3d)
        h = self.trunk(x)                             # (B, 2d)

        # Heads
        out = {name: self.heads[name](h).squeeze(1) for name in self.targets}
        out["attn_teammates"] = attn
        return out
