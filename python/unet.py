import pdb

import torch

model = torch.hub.load(
    "mateuszbuda/brain-segmentation-pytorch",
    "unet",
    in_channels=3,
    out_channels=1,
    init_features=32,
    pretrained=True,
)


# Download an example image
import urllib

url, filename = (
    "https://github.com/mateuszbuda/brain-segmentation-pytorch/raw/master/assets/TCGA_CS_4944.png",
    "TCGA_CS_4944.png",
)
try:
    urllib.URLopener().retrieve(url, filename)
except:
    urllib.request.urlretrieve(url, filename)


import numpy as np
from PIL import Image
from torchvision import transforms

input_image = Image.open(filename)
input_image.show()

m, s = np.mean(input_image, axis=(0, 1)), np.std(input_image, axis=(0, 1))
preprocess = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize(mean=m, std=s),
    ]
)
input_tensor = preprocess(input_image)
input_batch = input_tensor.unsqueeze(0)

if torch.cuda.is_available():
    input_batch = input_batch.to("cuda")
    model = model.to("cuda")

with torch.no_grad():
    output = model(input_batch)

print(torch.round(output[0]))

pdb.set_trace()

# import matplotlib.pyplot as plt
# plt.imshow(output[0].cpu())
# plt.show()
