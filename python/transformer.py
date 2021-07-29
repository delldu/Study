#! /usr/bin/env python
# coding=utf-8
#
# /************************************************************************************
# ***
# ***    File Author: Dell, 2019年 08月 20日 星期二 20:57:13 CST
# ***
# ************************************************************************************/
#
# https://www.cnblogs.com/guoyaohua/p/transformer.html
# https://github.com/harvardnlp/annotated-transformer


import pdb
import inspect

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import copy
import time
from torch.autograd import Variable
import matplotlib.pyplot as plt

import seaborn

seaborn.set_context(context="talk")


def debug(message):
    """Print the current line number with message."""

    callerframerecord = inspect.stack()[1]
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)
    # info.function
    print("Debug: {}, {}: {}".format(info.filename, info.lineno, message))


class EncoderDecoder(nn.Module):
    """
    A standard Encoder-Decoder architecture. Base for this and many
    other models.
    """

    def __init__(self, encoder, decoder, src_embed, tgt_embed, generator):
        super(EncoderDecoder, self).__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.src_embed = src_embed
        self.tgt_embed = tgt_embed
        self.generator = generator
        debug("src_embed: {}, {}".format(type(src_embed), src_embed))
        debug("tgt_embed: {}, {}".format(type(tgt_embed), tgt_embed))

    def forward(self, src, tgt, src_mask, tgt_mask):
        "Take in and process masked src and target sequences."
        return self.decode(self.encode(src, src_mask), src_mask, tgt, tgt_mask)

    def encode(self, src, src_mask):
        return self.encoder(self.src_embed(src), src_mask)

    def decode(self, memory, src_mask, tgt, tgt_mask):
        # memory = model.encode(src, src_mask)
        return self.decoder(self.tgt_embed(tgt), memory, src_mask, tgt_mask)


class Generator(nn.Module):
    "Define standard linear + softmax generation step."

    def __init__(self, d_model, vocab):
        super(Generator, self).__init__()
        self.proj = nn.Linear(d_model, vocab)

    def forward(self, x):
        return F.log_softmax(self.proj(x), dim=-1)


def clones(module, N):
    "Produce N identical layers."
    return nn.ModuleList([copy.deepcopy(module) for _ in range(N)])


class Encoder(nn.Module):
    "Core encoder is a stack of N layers"

    def __init__(self, layer, N):
        super(Encoder, self).__init__()
        self.layers = clones(layer, N)
        self.norm = LayerNorm(layer.size)

    def forward(self, x, mask):
        "Pass the input (and mask) through each layer in turn."
        for layer in self.layers:
            x = layer(x, mask)
        return self.norm(x)


class LayerNorm(nn.Module):
    "Construct a layernorm module (See citation for details)."

    def __init__(self, features, eps=1e-6):
        super(LayerNorm, self).__init__()
        self.a_2 = nn.Parameter(torch.ones(features))
        self.b_2 = nn.Parameter(torch.zeros(features))
        self.eps = eps

    def forward(self, x):
        mean = x.mean(-1, keepdim=True)
        std = x.std(-1, keepdim=True)
        return self.a_2 * (x - mean) / (std + self.eps) + self.b_2


class SublayerConnection(nn.Module):
    """
    A residual connection followed by a layer norm.
    Note for code simplicity the norm is first as opposed to last.
    """

    def __init__(self, size, dropout):
        super(SublayerConnection, self).__init__()
        self.norm = LayerNorm(size)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, sublayer):
        "Apply residual connection to any sublayer with the same size."
        return x + self.dropout(sublayer(self.norm(x)))


class EncoderLayer(nn.Module):
    "Encoder is made up of self-attn and feed forward (defined below)"

    def __init__(self, size, self_attn, feed_forward, dropout):
        super(EncoderLayer, self).__init__()
        self.self_attn = self_attn
        self.feed_forward = feed_forward
        self.sublayer = clones(SublayerConnection(size, dropout), 2)
        self.size = size

    def forward(self, x, mask):
        "Follow Figure 1 (left) for connections."
        x = self.sublayer[0](x, lambda x: self.self_attn(x, x, x, mask))
        return self.sublayer[1](x, self.feed_forward)


class Decoder(nn.Module):
    "Generic N layer decoder with masking."

    def __init__(self, layer, N):
        super(Decoder, self).__init__()
        self.layers = clones(layer, N)
        self.norm = LayerNorm(layer.size)

    def forward(self, x, memory, src_mask, tgt_mask):
        for layer in self.layers:
            x = layer(x, memory, src_mask, tgt_mask)
        # pdb.set_trace()
        # (Pdb) pp x.shape, memory.shape, src_mask.shape, tgt_mask.shape
        # (torch.Size([30, 9, 512]),
        #  torch.Size([30, 10, 512]),
        #  torch.Size([30, 1, 10]),
        #  torch.Size([30, 9, 9]))
        return self.norm(x)


class DecoderLayer(nn.Module):
    "Decoder is made of self-attn, src-attn, and feed forward (defined below)"

    def __init__(self, size, self_attn, src_attn, feed_forward, dropout):
        super(DecoderLayer, self).__init__()
        self.size = size
        self.self_attn = self_attn
        self.src_attn = src_attn
        self.feed_forward = feed_forward
        self.sublayer = clones(SublayerConnection(size, dropout), 3)

    def forward(self, x, memory, src_mask, tgt_mask):
        "Follow Figure 1 (right) for connections."
        m = memory
        x = self.sublayer[0](x, lambda x: self.self_attn(x, x, x, tgt_mask))
        x = self.sublayer[1](x, lambda x: self.src_attn(x, m, m, src_mask))
        return self.sublayer[2](x, self.feed_forward)


def subsequent_mask(size):
    "Mask out subsequent positions."
    attn_shape = (1, size, size)
    subsequent_mask = np.triu(np.ones(attn_shape), k=1).astype("uint8")
    return torch.from_numpy(subsequent_mask) == 0


# plt.figure(figsize=(5, 5))
# plt.imshow(subsequent_mask(20)[0])
# plt.show()


def attention(query, key, value, mask=None, dropout=None):
    "Compute 'Scaled Dot Product Attention'"
    d_k = query.size(-1)
    scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(d_k)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)
    p_attn = F.softmax(scores, dim=-1)
    if dropout is not None:
        p_attn = dropout(p_attn)
    # pdb.set_trace()
    # (Pdb) pp query.shape, key.shape, value.shape, mask.shape, scores
    # (torch.Size([30, 8, 10, 64]),
    #  torch.Size([30, 8, 10, 64]),
    #  torch.Size([30, 8, 10, 64]),
    #  torch.Size([30, 1, 1, 10]))
    #  torch.Size([30, 8, 10, 10])
    return torch.matmul(p_attn, value), p_attn


class MultiHeadedAttention(nn.Module):
    def __init__(self, h, d_model, dropout=0.1):
        "Take in model size and number of heads."
        super(MultiHeadedAttention, self).__init__()
        assert d_model % h == 0
        self.d_k = d_model // h
        self.h = h
        self.linears = clones(nn.Linear(d_model, d_model), 4)
        self.attn = None
        self.dropout = nn.Dropout(p=dropout)
        # pdb.set_trace()
        # (Pdb) a
        # self = MultiHeadedAttention(
        #   (linears): ModuleList(
        #     (0): Linear(in_features=512, out_features=512, bias=True)
        #     (1): Linear(in_features=512, out_features=512, bias=True)
        #     (2): Linear(in_features=512, out_features=512, bias=True)
        #     (3): Linear(in_features=512, out_features=512, bias=True)
        #   )
        #   (dropout): Dropout(p=0.1, inplace=False)
        # )
        # h = 8
        # d_model = 512
        # dropout = 0.1

    def forward(self, query, key, value, mask=None):
        "Implements Figure 2"
        if mask is not None:
            mask = mask.unsqueeze(1)
        nbatches = query.size(0)

        # for l, x in zip(self.linears, (query, key, value)):
        #     lx = l(x)
        #     print("---- x.shape:", x.shape, "lx.shape:",lx.shape)
        # ---- x.shape: torch.Size([30, 10, 512]) lx.shape: torch.Size([30, 10, 512])
        # ---- x.shape: torch.Size([30, 10, 512]) lx.shape: torch.Size([30, 10, 512])
        # ---- x.shape: torch.Size([30, 10, 512]) lx.shape: torch.Size([30, 10, 512])
        query, key, value = [
            l(x).view(nbatches, -1, self.h, self.d_k).transpose(1, 2)
            for l, x in zip(self.linears, (query, key, value))
        ]

        x, self.attn = attention(query, key, value, mask=mask, dropout=self.dropout)

        x = x.transpose(1, 2).contiguous().view(nbatches, -1, self.h * self.d_k)
        # pdb.set_trace()
        # (Pdb) pp query.shape, key.shape, value.shape, mask.shape
        # (torch.Size([30, 8, 10, 64]),
        #  torch.Size([30, 8, 10, 64]),
        #  torch.Size([30, 8, 10, 64]),
        #  torch.Size([30, 1, 1, 10]))

        # (Pdb) x.shape
        # torch.Size([30, 10, 512])
        return self.linears[-1](x)


class PositionwiseFeedForward(nn.Module):
    "Implements FFN equation."

    def __init__(self, d_model, d_ff, dropout=0.1):
        super(PositionwiseFeedForward, self).__init__()
        self.w_1 = nn.Linear(d_model, d_ff)
        self.w_2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        return self.w_2(self.dropout(F.relu(self.w_1(x))))


class Embeddings(nn.Module):
    def __init__(self, vocab, d_model):
        super(Embeddings, self).__init__()
        self.lut = nn.Embedding(vocab, d_model)
        self.d_model = d_model

    def forward(self, x):
        return self.lut(x) * math.sqrt(self.d_model)


class PositionalEncoding(nn.Module):
    "Implement the PE function."

    def __init__(self, d_model, dropout, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * -(math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer("pe", pe)
        # pdb.set_trace()
        # (Pdb) a
        # self = PositionalEncoding(
        #   (dropout): Dropout(p=0, inplace=False)
        # )
        # d_model = 20
        # dropout = 0
        # max_len = 5000

        # (Pdb) pp pe.shape
        # torch.Size([1, 5000, 20])
        # (Pdb) pp position.shape
        # torch.Size([5000, 1])
        # (Pdb) pp div_term
        # tensor([1.0000e+00, 3.9811e-01, 1.5849e-01, 6.3096e-02, 2.5119e-02, 1.0000e-02,
        #         3.9811e-03, 1.5849e-03, 6.3096e-04, 2.5119e-04])
        # (Pdb) pp div_term.shape
        # torch.Size([10])

    def forward(self, x):
        x = x + Variable(self.pe[:, : x.size(1)], requires_grad=False)
        return self.dropout(x)


plt.figure(figsize=(15, 5))
pe = PositionalEncoding(20, 0)
y = pe.forward(Variable(torch.zeros(1, 100, 20)))
plt.plot(np.arange(100), y[0, :, 4:8].data.numpy())
plt.legend(["dim %d" % p for p in [4, 5, 6, 7]])
plt.show()

# pdb.set_trace()


def make_model(src_vocab, tgt_vocab, N=6, d_model=512, d_ff=2048, h=8, dropout=0.1):
    "Construct a model from hyperparameters."
    attn = MultiHeadedAttention(h, d_model)
    ff = PositionwiseFeedForward(d_model, d_ff, dropout)
    position = PositionalEncoding(d_model, dropout)
    model = EncoderDecoder(
        Encoder(
            EncoderLayer(d_model, copy.deepcopy(attn), copy.deepcopy(ff), dropout), N
        ),
        Decoder(
            DecoderLayer(
                d_model,
                copy.deepcopy(attn),
                copy.deepcopy(attn),
                copy.deepcopy(ff),
                dropout,
            ),
            N,
        ),
        nn.Sequential(Embeddings(src_vocab, d_model), copy.deepcopy(position)),
        nn.Sequential(Embeddings(tgt_vocab, d_model), copy.deepcopy(position)),
        Generator(d_model, tgt_vocab),
    )

    for p in model.parameters():
        if p.dim() > 1:
            nn.init.xavier_uniform(p)
    # pdb.set_trace()
    # (Pdb) a
    # src_vocab = 10
    # tgt_vocab = 10
    # N = 2
    # d_model = 512
    # d_ff = 2048
    # h = 8
    # dropout = 0.1
    return model


tmp_model = make_model(10, 10, 2)

# pdb.set_trace()


class Batch:
    "Object for holding a batch of data with mask during training."

    def __init__(self, src, trg=None, pad=0):
        self.src = src
        self.src_mask = (src != pad).unsqueeze(-2)
        if trg is not None:
            self.trg = trg[:, :-1]
            self.trg_y = trg[:, 1:]
            self.trg_mask = self.make_std_mask(self.trg, pad)
            self.ntokens = (self.trg_y != pad).data.sum()
        # pdb.set_trace()
        # (Pdb) pp src.shape, trg.shape
        # (torch.Size([30, 10]), torch.Size([30, 10]))
        # (Pdb) pp self.src_mask.shape
        # torch.Size([30, 1, 10])

    @staticmethod
    def make_std_mask(tgt, pad):
        "Create a mask to hide padding and future words."
        tgt_mask = (tgt != pad).unsqueeze(-2)
        # (Pdb) (tgt != pad).unsqueeze(-2).shape
        # torch.Size([30, 1, 9])
        tgt_mask = tgt_mask & Variable(
            subsequent_mask(tgt.size(-1)).type_as(tgt_mask.data)
        )
        # pdb.set_trace()

        # (Pdb) subsequent_mask(tgt.size(-1)).type_as(tgt_mask.data)
        # tensor([[[ True, False, False, False, False, False, False, False, False],
        #          [ True,  True, False, False, False, False, False, False, False],
        #          [ True,  True,  True, False, False, False, False, False, False],
        #          [ True,  True,  True,  True, False, False, False, False, False],
        #          [ True,  True,  True,  True,  True, False, False, False, False],
        #          [ True,  True,  True,  True,  True,  True, False, False, False],
        #          [ True,  True,  True,  True,  True,  True,  True, False, False],
        #          [ True,  True,  True,  True,  True,  True,  True,  True, False],
        #          [ True,  True,  True,  True,  True,  True,  True,  True,  True]]])
        # (Pdb) subsequent_mask(tgt.size(-1)).type_as(tgt_mask.data).shape
        # torch.Size([1, 9, 9])

        # (Pdb) pp tgt.shape
        # torch.Size([30, 9])
        # (Pdb) pp tgt_mask.shape
        # torch.Size([30, 9, 9])

        return tgt_mask


def run_epoch(data_iter, model, loss_compute):
    "Standard Training and Logging Function"
    start = time.time()
    total_tokens = 0
    total_loss = 0
    tokens = 0
    for i, batch in enumerate(data_iter):
        out = model.forward(batch.src, batch.trg, batch.src_mask, batch.trg_mask)
        loss = loss_compute(out, batch.trg_y, batch.ntokens)

        total_loss += loss
        total_tokens += batch.ntokens
        tokens += batch.ntokens
        if i % 50 == 1:
            elapsed = time.time() - start
            print("elapsed:", elapsed)

            if elapsed < 1:
                elapsed = 1
            # pdb.set_trace()

            print(
                "Epoch Step: %d Loss: %f Tokens per Sec: %.2f"
                % (i, loss / batch.ntokens, tokens / elapsed)
            )
            start = time.time()
            tokens = 0

    print("Next epoch ...")
    return total_loss / total_tokens


# global max_src_in_batch, max_tgt_in_batch


# def batch_size_fn(new, count, sofar):
#     "Keep augmenting batch and calculate total number of tokens + padding."
#     global max_src_in_batch, max_tgt_in_batch
#     if count == 1:
#         max_src_in_batch = 0
#         max_tgt_in_batch = 0
#     max_src_in_batch = max(max_src_in_batch, len(new.src))
#     max_tgt_in_batch = max(max_tgt_in_batch, len(new.trg) + 2)
#     src_elements = count * max_src_in_batch
#     tgt_elements = count * max_tgt_in_batch
#     return max(src_elements, tgt_elements)


class NoamOpt:
    "Optim wrapper that implements rate."

    def __init__(self, model_size, factor, warmup, optimizer):
        self.optimizer = optimizer
        self._step = 0
        self.warmup = warmup
        self.factor = factor
        self.model_size = model_size
        self._rate = 0

    def step(self):
        "Update parameters and rate"
        self._step += 1
        rate = self.rate()
        for p in self.optimizer.param_groups:
            p["lr"] = rate
        self._rate = rate
        self.optimizer.step()

    def rate(self, step=None):
        "Implement `lrate` above"
        if step is None:
            step = self._step
        return self.factor * (
            self.model_size ** (-0.5)
            * min(step ** (-0.5), step * self.warmup ** (-1.5))
        )


def get_std_opt(model):
    return NoamOpt(
        model.src_embed[0].d_model,
        2,
        4000,
        torch.optim.Adam(model.parameters(), lr=0, betas=(0.9, 0.98), eps=1e-9),
    )


opts = [
    NoamOpt(512, 1, 4000, None),
    NoamOpt(512, 1, 8000, None),
    NoamOpt(256, 1, 4000, None),
]
plt.plot(np.arange(1, 20000), [[opt.rate(i) for opt in opts] for i in range(1, 20000)])
plt.legend(["512:4000", "512:8000", "256:4000"])
plt.show()

# pdb.set_trace()


class LabelSmoothing(nn.Module):
    "Implement label smoothing."

    def __init__(self, size, padding_idx, smoothing=0.0):
        super(LabelSmoothing, self).__init__()
        self.criterion = nn.KLDivLoss(size_average=False)
        self.padding_idx = padding_idx
        self.confidence = 1.0 - smoothing
        self.smoothing = smoothing
        self.size = size
        self.true_dist = None
        # pdb.set_trace()
        # self = LabelSmoothing(
        #   (criterion): KLDivLoss()
        # )
        # size = 5
        # padding_idx = 0
        # smoothing = 0.4

    def forward(self, x, target):
        assert x.size(1) == self.size
        true_dist = x.data.clone()
        true_dist.fill_(self.smoothing / (self.size - 2))
        true_dist.scatter_(1, target.data.unsqueeze(1), self.confidence)
        true_dist[:, self.padding_idx] = 0
        mask = torch.nonzero(target.data == self.padding_idx)
        if mask.dim() > 0:
            true_dist.index_fill_(0, mask.squeeze(), 0.0)
        self.true_dist = true_dist
        # pdb.set_trace()
        # (Pdb) x.shape
        # torch.Size([3, 5])
        # (Pdb) a
        # self = LabelSmoothing(
        #   (criterion): KLDivLoss()
        # )
        # x = tensor([[   -inf, -1.6094, -0.3567, -2.3026,    -inf],
        #         [   -inf, -1.6094, -0.3567, -2.3026,    -inf],
        #         [   -inf, -1.6094, -0.3567, -2.3026,    -inf]])
        # target = tensor([2, 1, 0])

        return self.criterion(x, Variable(true_dist, requires_grad=False))


crit = LabelSmoothing(5, 0, 0.4)
predict = torch.FloatTensor(
    [[0, 0.2, 0.7, 0.1, 0], [0, 0.2, 0.7, 0.1, 0], [0, 0.2, 0.7, 0.1, 0]]
)
v = crit(Variable(predict.log()), Variable(torch.LongTensor([2, 1, 0])))

plt.imshow(crit.true_dist)
plt.show()
# pdb.set_trace()

crit = LabelSmoothing(5, 0, 0.1)


def loss(x):
    d = x + 3 * 1
    predict = torch.FloatTensor(
        [
            [0, x / d, 1 / d, 1 / d, 1 / d],
        ]
    )
    return crit(Variable(predict.log()), Variable(torch.LongTensor([1]))).item()


# data[0]

plt.plot(np.arange(1, 100), [loss(x) for x in range(1, 100)])
plt.show()

# pdb.set_trace()


def data_gen(V, batch, nbatches):
    "Generate random data for a src-tgt copy task."
    for i in range(nbatches):
        data = torch.from_numpy(np.random.randint(1, V, size=(batch, 10)))
        data[:, 0] = 1
        src = Variable(data, requires_grad=False)
        tgt = Variable(data, requires_grad=False)
        yield Batch(src, tgt, 0)


class SimpleLossCompute:
    "A simple loss compute and train function."

    def __init__(self, generator, criterion, opt=None):
        self.generator = generator
        self.criterion = criterion
        self.opt = opt

    def __call__(self, x, y, norm):
        x = self.generator(x)
        loss = (
            self.criterion(x.contiguous().view(-1, x.size(-1)), y.contiguous().view(-1))
            / norm
        )
        loss.backward()
        if self.opt is not None:
            self.opt.step()
            self.opt.optimizer.zero_grad()
        # return loss.data[0] * norm
        return loss.item() * norm


print("Start Training ...")
V = 11

criterion = LabelSmoothing(size=V, padding_idx=0, smoothing=0.0)

model = make_model(V, V, N=2)

model_opt = NoamOpt(
    model.src_embed[0].d_model,
    1,
    400,
    torch.optim.Adam(model.parameters(), lr=0, betas=(0.9, 0.98), eps=1e-9),
)

for epoch in range(10):
    model.train()
    run_epoch(
        data_gen(V, 30, 20),
        model,
        SimpleLossCompute(model.generator, criterion, model_opt),
    )

    model.eval()
    print(
        run_epoch(
            data_gen(V, 30, 5),
            model,
            SimpleLossCompute(model.generator, criterion, None),
        )
    )


def greedy_decode(model, src, src_mask, max_len, start_symbol):
    memory = model.encode(src, src_mask)
    ys = torch.ones(1, 1).fill_(start_symbol).type_as(src.data)
    for i in range(max_len - 1):
        out = model.decode(
            memory,
            src_mask,
            Variable(ys),
            Variable(subsequent_mask(ys.size(1)).type_as(src.data)),
        )
        prob = model.generator(out[:, -1])
        _, next_word = torch.max(prob, dim=1)
        next_word = next_word.data[0]
        ys = torch.cat([ys, torch.ones(1, 1).type_as(src.data).fill_(next_word)], dim=1)

    pdb.set_trace()
    # src = tensor([[ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10]])
    # src_mask = tensor([[[1., 1., 1., 1., 1., 1., 1., 1., 1., 1.]]])
    # max_len = 10
    # start_symbol = 1
    # (Pdb) pp ys
    # tensor([[ 1,  2,  4,  5,  4,  6,  7,  8,  9, 10]])
    # (Pdb) pp ys.shape
    # torch.Size([1, 10])

    return ys


print("Evalation ...")
model.eval()
src = Variable(torch.LongTensor([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]))
src_mask = Variable(torch.ones(1, 1, 10))
print(greedy_decode(model, src, src_mask, max_len=10, start_symbol=1))
# pdb.set_trace()

exit()

# from torchtext import data, datasets

# # if True:
# if False:
#     import spacy
#     spacy_de = spacy.load('de')
#     spacy_en = spacy.load('en')

#     def tokenize_de(text):
#         return [tok.text for tok in spacy_de.tokenizer(text)]

#     def tokenize_en(text):
#         return [tok.text for tok in spacy_en.tokenizer(text)]

#     BOS_WORD = '<s>'
#     EOS_WORD = '</s>'
#     BLANK_WORD = "<blank>"
#     SRC = data.Field(tokenize=tokenize_de, pad_token=BLANK_WORD)
#     TGT = data.Field(
#         tokenize=tokenize_en,
#         init_token=BOS_WORD,
#         eos_token=EOS_WORD,
#         pad_token=BLANK_WORD)

#     MAX_LEN = 100
#     train, val, test = datasets.IWSLT.splits(
#         exts=('.de', '.en'),
#         fields=(SRC, TGT),
#         filter_pred=lambda x: len(vars(x)['src']) <= MAX_LEN and len(
#             vars(x)['trg']) <= MAX_LEN)
#     MIN_FREQ = 2
#     SRC.build_vocab(train.src, min_freq=MIN_FREQ)
#     TGT.build_vocab(train.trg, min_freq=MIN_FREQ)


# class MyIterator(data.Iterator):
#     def create_batches(self):
#         if self.train:

#             def pool(d, random_shuffler):
#                 for p in data.batch(d, self.batch_size * 100):
#                     p_batch = data.batch(
#                         sorted(p, key=self.sort_key), self.batch_size,
#                         self.batch_size_fn)
#                     for b in random_shuffler(list(p_batch)):
#                         yield b

#             self.batches = pool(self.data(), self.random_shuffler)

#         else:
#             self.batches = []
#             for b in data.batch(self.data(), self.batch_size,
#                                 self.batch_size_fn):
#                 self.batches.append(sorted(b, key=self.sort_key))


# def rebatch(pad_idx, batch):
#     "Fix order in torchtext to match ours"
#     src, trg = batch.src.transpose(0, 1), batch.trg.transpose(0, 1)
#     return Batch(src, trg, pad_idx)


# class MultiGPULossCompute:
#     "A multi-gpu loss compute and train function."

#     def __init__(self, generator, criterion, devices, opt=None, chunk_size=5):
#         self.generator = generator
#         self.criterion = nn.parallel.replicate(criterion, devices=devices)
#         self.opt = opt
#         self.devices = devices
#         self.chunk_size = chunk_size

#     def __call__(self, out, targets, normalize):
#         total = 0.0
#         generator = nn.parallel.replicate(self.generator, devices=self.devices)
#         out_scatter = nn.parallel.scatter(out, target_gpus=self.devices)
#         out_grad = [[] for _ in out_scatter]
#         targets = nn.parallel.scatter(targets, target_gpus=self.devices)

#         chunk_size = self.chunk_size
#         for i in range(0, out_scatter[0].size(1), chunk_size):
#             out_column = [[
#                 Variable(
#                     o[:, i:i + chunk_size].data,
#                     requires_grad=self.opt is not None)
#             ] for o in out_scatter]
#             gen = nn.parallel.parallel_apply(generator, out_column)

#             y = [(g.contiguous().view(-1, g.size(-1)),
#                   t[:, i:i + chunk_size].contiguous().view(-1))
#                  for g, t in zip(gen, targets)]
#             loss = nn.parallel.parallel_apply(self.criterion, y)

#             l = nn.parallel.gather(loss, target_device=self.devices[0])
#             l = l.sum()[0] / normalize
#             total += l.data[0]

#             if self.opt is not None:
#                 l.backward()
#                 for j, l in enumerate(loss):
#                     out_grad[j].append(out_column[j][0].grad.data.clone())

#         if self.opt is not None:
#             out_grad = [Variable(torch.cat(og, dim=1)) for og in out_grad]
#             o1 = out
#             o2 = nn.parallel.gather(out_grad, target_device=self.devices[0])
#             o1.backward(gradient=o2)
#             self.opt.step()
#             self.opt.optimizer.zero_grad()
#         return total * normalize


# devices = [0, 1, 2, 3]
# # if True:
# if False:
#     pad_idx = TGT.vocab.stoi["<blank>"]
#     model = make_model(len(SRC.vocab), len(TGT.vocab), N=6)
#     model.cuda()
#     criterion = LabelSmoothing(
#         size=len(TGT.vocab), padding_idx=pad_idx, smoothing=0.1)
#     criterion.cuda()
#     BATCH_SIZE = 12000
#     train_iter = MyIterator(
#         train,
#         batch_size=BATCH_SIZE,
#         device=0,
#         repeat=False,
#         sort_key=lambda x: (len(x.src), len(x.trg)),
#         batch_size_fn=batch_size_fn,
#         train=True)
#     valid_iter = MyIterator(
#         val,
#         batch_size=BATCH_SIZE,
#         device=0,
#         repeat=False,
#         sort_key=lambda x: (len(x.src), len(x.trg)),
#         batch_size_fn=batch_size_fn,
#         train=False)
#     model_par = nn.DataParallel(model, device_ids=devices)

# if False:
#     model_opt = NoamOpt(
#         model.src_embed[0].d_model, 1, 2000,
#         torch.optim.Adam(
#             model.parameters(), lr=0, betas=(0.9, 0.98), eps=1e-9))
#     for epoch in range(10):
#         model_par.train()
#         run_epoch((rebatch(pad_idx, b) for b in train_iter), model_par,
#                   MultiGPULossCompute(
#                       model.generator,
#                       criterion,
#                       devices=devices,
#                       opt=model_opt))
#         model_par.eval()
#         loss = run_epoch((rebatch(pad_idx, b) for b in valid_iter), model_par,
#                          MultiGPULossCompute(
#                              model.generator,
#                              criterion,
#                              devices=devices,
#                              opt=None))
#         print(loss)
# else:
#     model = torch.load("iwslt.pt")

# for i, batch in enumerate(valid_iter):
#     src = batch.src.transpose(0, 1)[:1]
#     src_mask = (src != SRC.vocab.stoi["<blank>"]).unsqueeze(-2)
#     out = greedy_decode(
#         model, src, src_mask, max_len=60, start_symbol=TGT.vocab.stoi["<s>"])
#     print("Translation:", end="\t")
#     for i in range(1, out.size(1)):
#         sym = TGT.vocab.itos[out[0, i]]
#         if sym == "</s>": break
#         print(sym, end=" ")
#     print()
#     print("Target:", end="\t")
#     for i in range(1, batch.trg.size(0)):
#         sym = TGT.vocab.itos[batch.trg.data[i, 0]]
#         if sym == "</s>": break
#         print(sym, end=" ")
#     print()
#     break

# if False:
#     model.src_embed[0].lut.weight = model.tgt_embeddings[0].lut.weight
#     model.generator.lut.weight = model.tgt_embed[0].lut.weight


# def average(model, models):
#     "Average models into model"
#     for ps in zip(*[m.params() for m in [model] + models]):
#         ps[0].copy_(torch.sum(*ps[1:]) / len(ps[1:]))


# model, SRC, TGT = torch.load("en-de-model.pt")

# model.eval()
# sent = "▁The ▁log ▁file ▁can ▁be ▁sent ▁secret ly ▁with ▁email ▁or ▁FTP ▁to ▁a ▁specified ▁receiver".split(
# )
# src = torch.LongTensor([[SRC.stoi[w] for w in sent]])
# src = Variable(src)
# src_mask = (src != SRC.stoi["<blank>"]).unsqueeze(-2)
# out = greedy_decode(
#     model, src, src_mask, max_len=60, start_symbol=TGT.stoi["<s>"])
# print("Translation:", end="\t")
# trans = "<s> "
# for i in range(1, out.size(1)):
#     sym = TGT.itos[out[0, i]]
#     if sym == "</s>": break
#     trans += sym + " "
# print(trans)

# tgt_sent = trans.split()


# def draw(data, x, y, ax):
#     seaborn.heatmap(
#         data,
#         xticklabels=x,
#         square=True,
#         yticklabels=y,
#         vmin=0.0,
#         vmax=1.0,
#         cbar=False,
#         ax=ax)


# for layer in range(1, 6, 2):
#     fig, axs = plt.subplots(1, 4, figsize=(20, 10))
#     print("Encoder Layer", layer + 1)
#     for h in range(4):
#         draw(
#             model.encoder.layers[layer].self_attn.attn[0, h].data,
#             sent,
#             sent if h == 0 else [],
#             ax=axs[h])
#     plt.show()

# for layer in range(1, 6, 2):
#     fig, axs = plt.subplots(1, 4, figsize=(20, 10))
#     print("Decoder Self Layer", layer + 1)
#     for h in range(4):
#         draw(
#             model.decoder.layers[layer].self_attn.attn[0, h].
#             data[:len(tgt_sent), :len(tgt_sent)],
#             tgt_sent,
#             tgt_sent if h == 0 else [],
#             ax=axs[h])
#     plt.show()
#     print("Decoder Src Layer", layer + 1)
#     fig, axs = plt.subplots(1, 4, figsize=(20, 10))
#     for h in range(4):
#         draw(
#             model.decoder.layers[layer].self_attn.attn[0, h].
#             data[:len(tgt_sent), :len(sent)],
#             sent,
#             tgt_sent if h == 0 else [],
#             ax=axs[h])
#     plt.show()
