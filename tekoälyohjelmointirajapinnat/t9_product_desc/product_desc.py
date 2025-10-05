from flask import Flask, render_template, request, jsonify
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Clean uploads folder on start
for filename in os.listdir(UPLOAD_FOLDER):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.isfile(filepath):
        os.remove(filepath)

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
            filename = str(uuid.uuid4()) + ".png"
            filepath = os.path.join(f"{UPLOAD_FOLDER}/{filename}")
            file.save(filepath)
            saved_files.append(filename)
            print(f"Saved: {filepath}")

    if not saved_files:
        return jsonify({"error": "no valid files uploaded"}), 400

    # Here you would pass `saved_files` to your image-to-text/LLM pipeline
    return jsonify({"success": True, "id": filename})

@app.route(f"/delete", methods=["POST"])
def remove_file():
    data = request.get_json()

    if not data or "id" not in data:
        return jsonify({"error": "no file found"}), 400
    
    server_id = data["id"]
    filepath = os.path.join(f"{UPLOAD_FOLDER}/{server_id}")

    try:
        os.remove(filepath)
    except Exception as e:
        return jsonify({"error": "delete failed", "detail": str(e)}), 500
    
    return jsonify({"success": True, "id": server_id})

@app.route("/generate", methods=["POST"])
def generate():
    # Placeholder for LLM generation
    product_details = request.form.get('details', '')
    
    description = f"Generated description for: {product_details[:50]}..." if product_details else "No details provided."
    return jsonify({"description": description})

if __name__ == '__main__':
    app.run(debug=True)
