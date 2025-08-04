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


def generate_causal_mask(seq_len):
    return torch.triu(torch.full((seq_len, seq_len), float('-inf')), diagonal=1)


class TransformerDecoderModel(nn.Module):
    def __init__(self, input_dim, model_dim, num_heads, num_layers, dropout, output_dim):
        super().__init__()
        self.model_dim = model_dim
        self.input_proj = nn.Linear(input_dim, model_dim)
        self.pos_encoder = PositionalEncoding(model_dim)

        encoder_layer = nn.TransformerEncoderLayer(d_model=model_dim, nhead=num_heads, dropout=dropout, batch_first=True)
        self.encoder_stack = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.output_layer = nn.Linear(model_dim, output_dim)

    def forward(self, x):
        # x: (batch_size, seq_len, input_dim)
        x = self.input_proj(x)  # project to model_dim
        x = self.pos_encoder(x)

        seq_len = x.size(1)
        mask = generate_causal_mask(seq_len).to(x.device)

        x = self.encoder_stack(x, mask)
        return self.output_layer(x)


# Example usage
if __name__ == '__main__':
    model = TransformerDecoderModel(
        input_dim=64,
        model_dim=128,
        num_heads=8,
        num_layers=4,
        dropout=0.1,
        output_dim=64
    )

    dummy_input = torch.randn(32, 10, 64)
    output = model(dummy_input)
    print(output.shape)