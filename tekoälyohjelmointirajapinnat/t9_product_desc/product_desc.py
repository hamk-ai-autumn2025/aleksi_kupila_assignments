from flask import Flask, render_template, request, jsonify
import os, base64, uuid
from werkzeug.utils import secure_filename
from openai import OpenAI

client = OpenAI()

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

def encode_image(image_path):
    '''
    Used by generateDescription
    '''
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8").replace("\n", "")
    except Exception as e:
        print(f'Invalid image path: {e}')
        return False
    
def generate_marketing_material(image_paths, prompt, model):
    '''
    Function for generating a marketing speech and 3 slogans for a product
    '''
    supports_sampling = model not in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
    print("---Generating description of image...---")
    print(f"---Using description generation model: {model}---\n")

    sysprompt = """You are a marketing assistant. 
    Given an image/images of a product and optional user input about its features or target audience, generate:

    1. A 3-4 sentence "sales speech" that highlights the product's main benefits and appeals to customers. 
    2. Three short, catchy marketing slogans (1-6 words each).

    Always return the result in JSON format like this:

    {
        "description": "...",
        "slogans": ["...", "...", "..."]
    }

    Do not include any text outside of the JSON object."""

    for img in image_paths:
        base64_image = encode_image(img)

    if base64_image:
        try:
            response = client.responses.create(
                instructions = sysprompt,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": f"{prompt}"
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        ]
                    }
                ],
                model=model,
                **({"temperature": 0.6, "top_p": 0.95} if supports_sampling else {}),  # Only enter these if model is not GPT-5 (supports sampling)
                max_output_tokens=2000,
            )
            # Prints output for both GPT-5 and others
            print(f"Response:\n{response.output_text}\n")
            return response.output_text

        except Exception as e:
            print(f"Error generating description: {e}\n")
    return False