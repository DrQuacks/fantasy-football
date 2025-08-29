import torch, torch.nn as nn

class MLP(nn.Module):
    def __init__(self, d_in, d_hidden=128, d_out=64, dropout=0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, d_hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(d_hidden, d_out), nn.ReLU()
        )
    def forward(self, x): return self.net(x)

class BucketedCrossAttention(nn.Module):
    """Query = player embedding; Keys/Values = teammate embeddings (+ slot embeddings)."""
    def __init__(self, d_model=64, num_heads=4):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
    def forward(self, q, T):  # q:(B,d), T:(B,N,d)
        q = q.unsqueeze(1)             # (B,1,d)
        out, weights = self.attn(q, T, T)  # (B,1,d), (B,1,N)
        return out.squeeze(1), weights.squeeze(1)  # (B,d), (B,N)
