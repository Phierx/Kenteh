import os
from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create user, gallery and item directories if they don’t exist
def create_gallery_path(user_id, item_name):
    gallery_path = os.path.join(app.config['UPLOAD_FOLDER'], user_id, 'gallery', item_name)
    os.makedirs(gallery_path, exist_ok=True)
    return gallery_path

@app.route('/upload', methods=['GET', 'POST'])
def upload_gallery():
    if request.method == 'POST':
        user_id = request.form.get('user_id')  # Example: "user123"
        item_name = request.form.get('item_name')  # Example: "kente_set"
        images = request.files.getlist('images')

        if not user_id or not item_name or not images:
            return "Missing user_id, item_name, or images", 400

        save_path = create_gallery_path(user_id, item_name)

        for image in images:
            if image and image.filename:
                filename = secure_filename(image.filename)
                image.save(os.path.join(save_path, filename))

        return f"Uploaded {len(images)} images to {item_name} for user {user_id}"
    
    return render_template('upload_form.html')
