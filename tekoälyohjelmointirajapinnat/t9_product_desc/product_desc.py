from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:  # Dropzone sends as 'image'
        return jsonify({"error": "no file part"}), 400

    uploaded_files = request.files.getlist("image")  # Handle multiple files

    if not uploaded_files:
        return jsonify({"error": "no selected files"}), 400

    saved_files = []
    for file in uploaded_files:
        if file.filename == "":
            continue
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(f"{UPLOAD_FOLDER}/{filename}")
            file.save(filepath)
            saved_files.append(filename)
            print(f"Saved: {filepath}")

    if not saved_files:
        return jsonify({"error": "no valid files uploaded"}), 400

    # Here you would pass `saved_files` to your image-to-text/LLM pipeline
    return jsonify({"success": True, "files": saved_files})

@app.route("/generate", methods=["POST"])
def generate():
    # Placeholder for LLM generation
    product_details = request.form.get('details', '')
    # In real implementation, process images and details with LLM
    description = f"Generated description for: {product_details[:50]}..." if product_details else "No details provided."
    return jsonify({"description": description})

if __name__ == '__main__':
    app.run(debug=True)
