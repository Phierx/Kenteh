import os
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import json

# Load ResNet model and prepare feature extractor
resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
resnet.eval()
feature_extractor = torch.nn.Sequential(*list(resnet.children())[:-1])

# Image preprocessing (consistent with search.py)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# Root folder where images are stored
root_folder = r"C:\xampp\htdocs\Kenteh\data"

for folder_name in os.listdir(root_folder):
    folder_path = os.path.join(root_folder, folder_name)
    if not os.path.isdir(folder_path):
        continue

    tags = {}

    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(folder_path, filename)
            image = Image.open(image_path).convert('RGB')
            tensor = transform(image).unsqueeze(0)

            with torch.no_grad():
                vector = feature_extractor(tensor).squeeze().numpy().reshape(1, -1)

            # Normalize to ensure consistent matching
            vector /= np.linalg.norm(vector)

            # Save vector as .npy
            vector_filename = filename.rsplit('.', 1)[0] + '.npy'
            vector_path = os.path.join(folder_path, vector_filename)
            np.save(vector_path, vector.astype(np.float32))

            tags[filename] = ["auto-tagged"]

    # Save tags.json in the current folder
    tags_path = os.path.join(folder_path, "tags.json")
    with open(tags_path, "w") as f:
        json.dump(tags, f, indent=4)

    print(f"✅ Processed: {folder_path}")
