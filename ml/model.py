import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=500):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1)]
        return x

class TransformerDecoderOnly(nn.Module):
    def __init__(self, input_dim, model_dim, num_heads, num_layers, dropout, output_dim, context_length, forecast_length, known_future_dim: int = 0):
        super().__init__()
        self.context_length = context_length
        self.forecast_length = forecast_length
        self.model_dim = model_dim

        self.input_proj = nn.Linear(input_dim, model_dim)
        self.output_proj = nn.Linear(model_dim, output_dim)

        self.positional_encoding = PositionalEncoding(model_dim)

        decoder_layer = nn.TransformerDecoderLayer(d_model=model_dim, nhead=num_heads, dropout=dropout, batch_first=True)
        self.decoder = nn.TransformerDecoder(decoder_layer, num_layers=num_layers)

        # Learnable query, optionally conditioned on known future features
        self.query_embed = nn.Parameter(torch.randn(1, forecast_length, model_dim))
        self.future_cond = None
        if known_future_dim and known_future_dim > 0:
            self.future_cond = nn.Linear(known_future_dim, model_dim)

    def forward(self, context, future_known=None, src_key_padding_mask=None):
        memory = self.input_proj(context)  # (B, context_len, D)
        memory = self.positional_encoding(memory)

        batch_size = memory.size(0)
        tgt = self.query_embed.expand(batch_size, -1, -1)  # (B, forecast_len, D)
        if self.future_cond is not None and future_known is not None and future_known.numel() > 0:
            cond = self.future_cond(future_known)  # (B, forecast_len, D)
            tgt = tgt + cond
        tgt = self.positional_encoding(tgt)

        tgt_mask = torch.triu(
            torch.full((self.forecast_length, self.forecast_length), float('-inf')),
            diagonal=1
        ).to(memory.device)

        decoded = self.decoder(
            tgt=tgt,
            memory=memory,
            tgt_mask=tgt_mask,
            memory_key_padding_mask=src_key_padding_mask
        )

        return torch.relu(self.output_proj(decoded))

# Example usage
if __name__ == '__main__':
    model = TransformerDecoderOnly(
        input_dim=64,
        model_dim=128,
        num_heads=4,
        num_layers=3,
        dropout=0.1,
        output_dim=64,
        context_length=12,
        forecast_length=4
    )

    dummy_input = torch.randn(32, 12, 64)
    out = model(dummy_input)
    print(out.shape)  # (32, 4, 64)
