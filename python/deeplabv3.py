import pdb
import time
from tqdm import tqdm

import torch

model = torch.hub.load("pytorch/vision:v0.6.0", "deeplabv3_resnet101", pretrained=True)
model.eval()
print(model)

# sample execution (requires torchvision)
from PIL import Image
from torchvision import transforms

# input_image = Image.open(filename)
filename = "dog.jpg"
input_image = Image.open(filename).convert("RGB")
input_image.show()

preprocess = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

input_tensor = preprocess(input_image)
input_batch = input_tensor.unsqueeze(0)  # create a mini-batch as expected by the model

# move the input and model to GPU for speed if available
if torch.cuda.is_available():
    input_batch = input_batch.to("cuda")
    model.to("cuda")

model.eval()
start = time.time()

for i in tqdm(range(100)):
    with torch.no_grad():
        output = model(input_batch)["out"][0]

print("Speend time: {}".format(time.time() - start))


output_predictions = output.argmax(0)

palette = torch.tensor([2 ** 25 - 1, 2 ** 15 - 1, 2 ** 21 - 1])
colors = torch.as_tensor([i for i in range(21)])[:, None] * palette
colors = (colors % 255).numpy().astype("uint8")

# plot the semantic segmentation predictions of 21 classes in each color
r = Image.fromarray(output_predictions.byte().cpu().numpy()).resize(input_image.size)
r.putpalette(colors)

import matplotlib.pyplot as plt

plt.imshow(r)
plt.show()

# pdb.set_trace()
