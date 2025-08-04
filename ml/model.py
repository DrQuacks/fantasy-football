import torch
import torch.nn as nn
import torch.nn.functional as F

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=500):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-torch.log(torch.tensor(10000.0)) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # shape (1, max_len, d_model)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1)]
        return x


def generate_causal_mask(size):
    mask = torch.triu(torch.ones(size, size) * float('-inf'), diagonal=1)
    return mask


class TransformerDecoderModel(nn.Module):
    def __init__(self, input_dim, model_dim, num_heads, num_layers, dropout, output_dim):
        super().__init__()
        self.model_dim = model_dim
        self.input_proj = nn.Linear(input_dim, model_dim)
        self.pos_encoder = PositionalEncoding(model_dim)

        decoder_layer = nn.TransformerDecoderLayer(d_model=model_dim, nhead=num_heads, dropout=dropout, batch_first=True)
        self.transformer_decoder = nn.TransformerDecoder(decoder_layer, num_layers=num_layers)

        self.output_layer = nn.Linear(model_dim, output_dim)

    def forward(self, tgt_seq, memory=None, tgt_mask=None):
        # tgt_seq: (batch_size, seq_len, input_dim)
        x = self.input_proj(tgt_seq)  # project to model_dim
        x = self.pos_encoder(x)

        # causal mask
        if tgt_mask is None:
            tgt_mask = generate_causal_mask(x.size(1)).to(x.device)

        output = self.transformer_decoder(tgt=x, memory=memory, tgt_mask=tgt_mask)
        return self.output_layer(output)  # shape: (batch_size, seq_len, output_dim)


# Example usage:
if __name__ == '__main__':
    model = TransformerDecoderModel(
        input_dim=64,  # number of input features
        model_dim=128,
        num_heads=8,
        num_layers=4,
        dropout=0.1,
        output_dim=64  # same as input_dim if predicting same fields
    )

    dummy_input = torch.randn(32, 10, 64)  # (batch, sequence_len, features)
    output = model(dummy_input)  # (32, 10, 64)
    print(output.shape)
