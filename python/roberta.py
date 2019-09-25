import torch
#roberta = torch.hub.load('pytorch/fairseq', 'roberta.large')
roberta = torch.hub.load('pytorch/fairseq', 'roberta.base')
roberta.eval()  # disable dropout (or leave in train mode to finetune)

print("model:", roberta)

tokens = roberta.encode('Hello world!')
# assert tokens.tolist() == [0, 31414, 232, 328, 2]
print(roberta.decode(tokens))



last_layer_features = roberta.extract_features(tokens)
assert last_layer_features.size() == torch.Size([1, 5, 1024])

# Extract all layer's features (layer 0 is the embedding layer)
all_layers = roberta.extract_features(tokens, return_all_hiddens=True)
assert len(all_layers) == 25
assert torch.all(all_layers[-1] == last_layer_features)
print("all_layers:", len(all_layers), all_layers[0].shape)
print("all_layers data:", all_layers)

# Download RoBERTa already finetuned for MNLI
roberta = torch.hub.load('pytorch/fairseq', 'roberta.large.mnli')
roberta.eval()  # disable dropout for evaluation

with torch.no_grad():
    # Encode a pair of sentences and make a prediction
    a = 'Roberta is heavily optimized version of BERT.'
    b = 'Roberta is not very optimized.'
    tokens = roberta.encode(a, b)
    prediction = roberta.predict('mnli', tokens).argmax().item()
    assert prediction == 0  # contradiction

    print("a: {}, b: {}, predict: {}".format(a, b, prediction))

    # Encode another pair of sentences
    a = 'Roberta is a heavily optimized version of BERT.'
    b = 'Roberta is based on BERT.'
    tokens = roberta.encode(a, b)
    prediction = roberta.predict('mnli', tokens).argmax().item()
    assert prediction == 2  # entailment
    print("a: {}, b: {}, predict: {}".format(a, b, prediction))


roberta.register_classification_head('new_task', num_classes=3)
logprobs = roberta.predict('new_task', tokens)  # tensor([[-1.1050, -1.0672, -1.1245]], grad_fn=<LogSoftmaxBackward>)
print("logprobs:", logprobs)

