import os
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import json
import numpy as np

# Load pretrained ResNet50 model
resnet = models.resnet50(pretrained=True)
resnet.eval()
feature_extractor = torch.nn.Sequential(*list(resnet.children())[:-1])  # Remove classifier

# Image transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# Load tags.json
with open(r"C:\Users\Admin\.conda\envs\fabric-organizer\data\output.old\tags.json", "r") as f:
    tags = json.load(f)

# Paths
image_dir = r"C:\Users\Admin\.conda\envs\fabric-organizer\data\output.old\images"
output_vectors = {}

# Process images
for filename in os.listdir(image_dir):
    if filename.endswith(('.jpg', '.jpeg', '.png')):
        path = os.path.join(image_dir, filename)
        image = Image.open(path).convert("RGB")
        input_tensor = transform(image).unsqueeze(0)

        with torch.no_grad():
            vector = feature_extractor(input_tensor).squeeze().numpy()

        # Store vector and tags
        output_vectors[filename] = {
            "vector": vector.tolist(),
            "tags": tags.get(filename, [])
        }

# Save as JSON
with open("image_vectors_with_tags.json", "w") as f:
    json.dump(output_vectors, f, indent=4)

print("Done. Vectors + tags saved.")
