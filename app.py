from flask import Flask, request, jsonify, render_template, send_from_directory
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
VECTOR_DB_PATH = r"C:\xampp\htdocs\Kenteh\data"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load ResNet model and prepare feature extractor
resnet = models.resnet50(weights=ResNet50_Weights.DEFAULT)
resnet.eval()
feature_extractor = torch.nn.Sequential(*list(resnet.children())[:-1])

# Image preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

def extract_vector(img_path):
    img = Image.open(img_path).convert("RGB")
    tensor = transform(img).unsqueeze(0)
    with torch.no_grad():
        vector = feature_extractor(tensor).squeeze().numpy()
    return vector.reshape(1, -1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(image_file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_file.save(file_path)

    query_vector = extract_vector(file_path)

    best_match = None
    best_match_image = None
    highest_score = -1

    for root, dirs, files in os.walk(VECTOR_DB_PATH):
        for file in files:
            if file.endswith(".npy"):
                vector_path = os.path.join(root, file)
                db_vector = np.load(vector_path).reshape(1, -1)
                score = cosine_similarity(query_vector, db_vector)[0][0]

                if score > highest_score:
                    highest_score = score
                    image_filename = file.replace('.npy', '.jpg')
                    best_match_image = os.path.join(root, image_filename)

    if best_match_image and os.path.exists(best_match_image):
        relative_path = os.path.relpath(best_match_image, VECTOR_DB_PATH)
        image_url = f"/matched/{relative_path.replace(os.sep, '/')}"

        return render_template("result.html", image_url=image_url, score=round(highest_score, 4))

    return jsonify({"error": "No match found"}), 404

@app.route('/matched/<path:filename>')
def serve_matched_image(filename):
    return send_from_directory(VECTOR_DB_PATH, filename)

if __name__ == '__main__':
    app.run(debug=True)
