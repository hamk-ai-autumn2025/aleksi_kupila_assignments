import json, re
from flask import Flask, request, render_template
from openai_apis import ask_model

app = Flask(__name__)

ALLOWED_TOOLS = {"nmap", "nikto"}

# --- Extract JSON file from AI output ---
def extract_json(text):
    try:
        return json.loads(text)
    except Exception:
        pass
    # try to find first [...] block
    m = re.search(r'(\[.*\])', text, re.S)
    if m:
        candidate = m.group(1)
        # try json
        try:
            return json.loads(candidate)
        except Exception:
            pass
    # give up
    raise ValueError("Could not parse JSON from model output")

# --- Validate JSON file structure
def validateStructure(commands):
    if not isinstance(commands, list):
        return False
    
    for cmd in commands:
        if not isinstance(cmd, dict) or "command" not in cmd or "tool" not in cmd:
            return False
        if cmd.get("tool") not in ALLOWED_TOOLS:
            return False
    return True

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', instruction = False)

@app.route('/suggest', methods=['POST'])
def suggest():
    instruction = request.form["instruction"]
    if instruction:
        command_suggestions = ask_model(instruction, 400)
        try:
            commands = extract_json(command_suggestions)
            if validateStructure(commands):
                return render_template('index.html', suggestion=commands, error=None)
            else:
                return render_template('index.html', suggestion=None, error=f"Failed to validate JSON structure\nAI raw: {commands}")
        except Exception as e:
            return render_template("index.html", suggestion=None, error=f"Failed to parse AI JSON: {e}\nAI raw: {command_suggestions}")
    return render_template('index.html', suggestion = None, error="Please enter instructions above")
