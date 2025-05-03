from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from torchvision.models import ResNet50_Weights

# Flask setup
app = Flask(__name__)

# Paths
UPLOAD_FOLDER = 'uploads'
VECTOR_DB_PATH = r"C:\xampp\htdocs\Kenteh\data"  # Path to vector database

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load ResNet model and prepare feature extractor
resnet = models.resnet50(weights=ResNet50_Weights.DEFAULT)
resnet.eval()
feature_extractor = torch.nn.Sequential(*list(resnet.children())[:-1])

# Image preprocessing transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# Function to extract image vector
def extract_vector(img_path):
    img = Image.open(img_path).convert("RGB")
    tensor = transform(img).unsqueeze(0)
    with torch.no_grad():
        vector = feature_extractor(tensor).squeeze().numpy()
    return vector.reshape(1, -1)

# Route for homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle image upload and search
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the uploaded image
    filename = secure_filename(image_file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    image_file.save(file_path)

    # Extract the query vector
    query_vector = extract_vector(file_path)

    # Search in the database
    best_match = None
    highest_score = -1

    for root, dirs, files in os.walk(VECTOR_DB_PATH):
        for file in files:
            if file.endswith(".npy"):
                vector_path = os.path.join(root, file)
                db_vector = np.load(vector_path).reshape(1, -1)
                score = cosine_similarity(query_vector, db_vector)[0][0]

                if score > highest_score:
                    highest_score = score
                    best_match = vector_path

    if best_match:
        # Ensure highest_score is a native Python float, not a numpy float32
        highest_score = float(highest_score)

        return jsonify({
            "best_match": best_match,
            "similarity_score": highest_score
        })
    else:
        return jsonify({"error": "No match found"}), 404


if __name__ == '__main__':
    app.run(debug=True)
