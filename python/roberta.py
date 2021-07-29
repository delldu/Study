import pdb

import torch


def basic():
    # roberta = torch.hub.load('pytorch/fairseq', 'roberta.large')
    roberta = torch.hub.load("pytorch/fairseq", "roberta.large")
    roberta.eval()  # disable dropout (or leave in train mode to finetune)

    print("roberta.large model:", roberta)

    tokens = roberta.encode("Hello world!")
    print(roberta.decode(tokens))

    pdb.set_trace()

    # (Pdb) pp tokens
    # tensor([    0, 31414,   232,   328,     2])
    last_layer_features = roberta.extract_features(tokens)
    # pdb.set_trace()
    # (Pdb) pp last_layer_features.shape
    # torch.Size([1, 5, 768])

    # Extract all layer's features (layer 0 is the embedding layer)
    all_layers = roberta.extract_features(tokens, return_all_hiddens=True)
    # (Pdb) type(all_layers), len(all_layers)
    # (<class 'list'>, 13)


basic()


# Download RoBERTa already finetuned for MNLI
roberta = torch.hub.load("pytorch/fairseq", "roberta.large.mnli")
roberta.eval()  # disable dropout for evaluation
print("roberta.large.mnli model:", roberta)

with torch.no_grad():
    # Encode a pair of sentences and make a prediction
    a = "Roberta is heavily optimized version of BERT."
    b = "Roberta is not very optimized."
    tokens = roberta.encode(a, b)
    prediction = roberta.predict("mnli", tokens).argmax().item()
    assert prediction == 0  # contradiction
    print("a: {}, b: {}, predict: {}".format(a, b, prediction))

    # Encode another pair of sentences
    a = "Roberta is a heavily optimized version of BERT."
    b = "Roberta is based on BERT."
    tokens = roberta.encode(a, b)
    prediction = roberta.predict("mnli", tokens).argmax().item()
    assert prediction == 2  # entailment
    print("a: {}, b: {}, predict: {}".format(a, b, prediction))

    a = "I love sea."
    b = "I like sea.."
    tokens = roberta.encode(a, b)
    prediction = roberta.predict("mnli", tokens).argmax().item()
    print("a: {}, b: {}, predict: {}".format(a, b, prediction))

    a = "I love sea."
    b = "I do not love sea."
    tokens = roberta.encode(a, b)
    prediction = roberta.predict("mnli", tokens).argmax().item()
    print("a: {}, b: {}, predict: {}".format(a, b, prediction))

    a = "I love sea."
    b = "I hate sea."
    tokens = roberta.encode(a, b)
    prediction = roberta.predict("mnli", tokens).argmax().item()
    print("a: {}, b: {}, predict: {}".format(a, b, prediction))

    a = "I love sea."
    b = "I hate sea, because it is too big."
    tokens = roberta.encode(a, b)
    prediction = roberta.predict("mnli", tokens).argmax().item()
    print("a: {}, b: {}, predict: {}".format(a, b, prediction))

    # a: 我喜欢大海., b: 我喜欢蓝蓝的海水., predict: 0
    # a: 我喜欢大海., b: 我不喜欢大海., predict: 1
    # a: 我喜欢大海., b: 我超级憎恨大海., predict: 0
    # a: 我喜欢大海., b: 我恨大海，恨得咬牙切齿., predict: 0

    # a: 我爱大海., b: 我喜欢蓝蓝的海水., predict: 0
    # a: 我爱大海., b: 我不喜欢大海., predict: 0
    # a: 我爱大海., b: 我超级憎恨大海., predict: 0
    # a: 我爱大海., b: 我恨大海，恨得咬牙切齿., predict: 0

    # a: 我Love大海., b: 我Like蓝蓝的海水., predict: 0
    # a: 我Love大海., b: 我Do not love大海., predict: 0
    # a: 我Love大海., b: 我Hate大海., predict: 0
    # a: 我Love大海., b: 我Hate大海，恨得咬牙切齿., predict: 0

    # a: I love sea., b: I like sea.., predict: 2
    # a: I love sea., b: I do not love sea., predict: 0
    # a: I love sea., b: I hate sea., predict: 0
    # a: I love sea., b: I hate sea, because it is too big., predict: 0


batch_of_pairs = [
    ["我 喜 欢 大 海.", "我 爱 大 海."],
    ["我 喜 欢 大 海.", "我 喜 欢 蓝 蓝 的 大 海."],
    ["我 喜 欢 大 海.", "我 不 喜 欢　大 海."],
    ["我 喜 欢 大 海.", "我 超级　憎 恨 大 海."],
    ["我 喜 欢 大 海.", "我 恨 大 海，恨 得 咬 牙 切 齿."],
    ["我 爱 大 海.", "我 喜 欢 大 海."],
    ["我 爱 大 海.", "我 不 喜 欢 大 海."],
    ["我 爱 大 海.", "我 超 级 憎 恨　大 海."],
    ["我 爱 大 海.", "我 恨 大 海，恨 得 咬 牙 切 齿."],
    ["我 love 大 海.", "我 like　蓝 蓝 的 大 海."],
    ["我 love 大 海.", "我 do not like 大 海."],
    ["我 love 大 海.", "我 hate 大 海."],
    ["我 love 大 海.", "我 hate 大 海，恨 得 咬 牙 切 齿."],
]

for (a, b) in batch_of_pairs:
    tokens = roberta.encode(a, b)
    prediction = roberta.predict("mnli", tokens).argmax().item()
    print("{} -- {} ==> {}".format(a, b, prediction))


# roberta.register_classification_head('new_task', num_classes=3)
# logprobs = roberta.predict('new_task', tokens)  # tensor([[-1.1050, -1.0672, -1.1245]], grad_fn=<LogSoftmaxBackward>)
# print("logprobs:", logprobs)
