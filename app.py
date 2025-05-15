from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
from auth import auth_bp, mysql

import os
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Flask setup
app = Flask(__name__)

# Secret key for session management (flash, login, etc.)
app.secret_key = 'your-super-secret-key'  # Replace with a strong secret key

# MySQL configuration (adjust based on your phpMyAdmin settings)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Leave empty if no password is set
app.config['MYSQL_DB'] = 'kenteh_db'  # Make sure this DB exists in phpMyAdmin

# Initialize MySQL with app
mysql.init_app(app)

# Register Blueprint
app.register_blueprint(auth_bp)

# Paths
UPLOAD_FOLDER = 'uploads'
VECTOR_DB_PATH = r"C:\xampp\htdocs\Kenteh\data"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load ResNet model and prepare feature extractor
resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
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
        vector = feature_extractor(tensor).squeeze().numpy().reshape(1, -1)

    vector /= np.linalg.norm(vector)
    return vector.astype(np.float32)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    firstname = session.get('firstname') or 'User'  # fallback if session is missing
    user_id = session.get('user_ID')
    return render_template('dashboard.html', firstname=firstname,user_id=user_id)

@app.route('/users')
def users():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM UsersProfile")
    users = cur.fetchall()
    cur.close()
    return str(users)


@app.route('/about')
def about():
    return render_template('about.html')  # You need to create templates/about.html

@app.route('/settings')
def settings():
    return render_template('settings.html')  # You need to create templates/settings.html

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO UsersProfile (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        mysql.connection.commit()
        cur.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM UsersProfile WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash(f"Welcome back, {user[1]}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/gallery/upload', methods=['GET', 'POST'])
def gallery_upload():
    if request.method == 'POST':
        user_id = session.get('user_id')  # ✅ get from session
        firstname = session.get('username')
        item_name = request.form['item_name']
        images = request.files.getlist('images')

        if not user_id or not item_name or not images:
            flash("Missing required fields", "error")
            return redirect(request.url)

        user_gallery_path = os.path.join(app.root_path, 'static', 'user_data', str(user_id), 'gallery', item_name)
        os.makedirs(user_gallery_path, exist_ok=True)

        for image in images:
            if image and image.filename:
                filename = secure_filename(image.filename)
                saved_path = os.path.join(user_gallery_path, filename)
                image.save(saved_path)

                # Save metadata to the database
                cur = mysql.connection.cursor()
                cur.execute("""
                    INSERT INTO imagedb (UserID, Title, Description, ImagePath, ActiveSearch)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    user_id,
                    item_name,
                    f"Gallery upload for {item_name}",  # You can customize this
                    saved_path.replace("\\", "/"),       # normalize Windows path slashes
                    1  # ActiveSearch = True
                ))
                mysql.connection.commit()
                cur.close()

        flash("Images uploaded to your gallery successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template("upload_form.html",
                           user_id=session.get("user_id"),
                           firstname=session.get("username"))



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

    best_match_image = None
    highest_score = -1

    for root, _, files in os.walk(VECTOR_DB_PATH):
        for file in files:
            if file.endswith(".npy"):
                vector_path = os.path.join(root, file)
                db_vector = np.load(vector_path).astype(np.float32).reshape(1, -1)

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

@app.route('/business_profile', methods=['POST'])
def save_business_profile():
    business_name = request.form['business_name']
    phone = request.form['phone']
    address = request.form['address']
    description = request.form['description']
    user_id = session.get('user_id')

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO BusinessProfile (UserID, BusinessName, Phone, Address, Description)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, business_name, phone, address, description))
    mysql.connection.commit()
    cur.close()

    flash('Business profile saved successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/matched/<path:filename>')
def serve_matched_image(filename):
    return send_from_directory(VECTOR_DB_PATH, filename)

if __name__ == '__main__':
    app.run(debug=True)
