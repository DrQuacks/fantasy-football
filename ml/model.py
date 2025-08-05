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
    def __init__(self, input_dim, model_dim, num_heads, num_layers, dropout, output_dim, context_length, forecast_length):
        super().__init__()
        self.context_length = context_length
        self.forecast_length = forecast_length
        self.model_dim = model_dim

        self.input_proj = nn.Linear(input_dim, model_dim)
        self.output_proj = nn.Linear(model_dim, output_dim)

        self.positional_encoding = PositionalEncoding(model_dim)

        decoder_layer = nn.TransformerDecoderLayer(d_model=model_dim, nhead=num_heads, dropout=dropout, batch_first=True)
        self.decoder = nn.TransformerDecoder(decoder_layer, num_layers=num_layers)

        self.query_embed = nn.Parameter(torch.randn(1, forecast_length, model_dim))

    def forward(self, context):
        # context: (batch_size, context_len, input_dim)
        memory = self.input_proj(context)  # (B, C, D)
        memory = self.positional_encoding(memory)

        # Expand forecast query embeddings to batch size
        batch_size = memory.size(0)
        tgt = self.query_embed.expand(batch_size, -1, -1)  # (B, forecast_len, D)
        tgt = self.positional_encoding(tgt)

        # Causal mask for decoder
        tgt_mask = torch.triu(torch.full((self.forecast_length, self.forecast_length), float('-inf')), diagonal=1).to(memory.device)

        decoded = self.decoder(tgt=tgt, memory=memory, tgt_mask=tgt_mask)  # (B, forecast_len, D)
        return self.output_proj(decoded)  # (B, forecast_len, output_dim)


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
