import json, re
from flask import Flask, request, render_template
from openai_apis import ask_model

app = Flask(__name__)

ALLOWED_TOOLS = {"nmap", "nikto"}
FORBIDDEN_CHARS = [";", "&", "|", "`", "$(", ">", "<"]

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

# --- Validate JSON file structure ---
def validateStructure(commands):
    if not isinstance(commands, list):
        return False
    
    for cmd in commands:
        if not isinstance(cmd, dict) or "command" not in cmd or "tool" not in cmd:
            return False
        if cmd.get("tool") not in ALLOWED_TOOLS:
            return False
    return True

# --- Basic command safety check ---
def valid_command(command):
    ALLOWED_TARGETS = ["dvwa", "poc_target", "localhost", "127.0.0.1"]
    # If command contains dangerous characters
    if any(ch in command for ch in FORBIDDEN_CHARS):
        return False, "Command contains forbidden characters"
    # check tool presence
    cmd_lower = command.strip().lower()
    if not any(cmd_lower.startswith(t + " ") or (" " + t + " ") in cmd_lower for t in ALLOWED_TOOLS):
        return False, "Command does not use an allowed tool"
    # Cheack if target machine is an allowed target
    if not any(t in command for t in ALLOWED_TARGETS):
        return False, "Command target not allowed; must target local test containers"
    return True, ""

# --- When user clicks "Get command suggestion" button
@app.route('/suggest', methods=['POST'])
def suggest():
    instruction = request.form["instruction"]
    if instruction:
        # Request LLM for a command
        command_suggestions = ask_model(instruction, 400)
        # If suggestion is EMPTY
        if command_suggestions == "[]":
            return render_template('index.html', suggestion=None, error=f"AI answer was empty. Maybe the prompt asked for a forbidden command?\nAI raw: {command_suggestions}")
        try:
            commands = extract_json(command_suggestions)  # Try extracting JSON 
            if validateStructure(commands):  # If JSON structure is valid
                return render_template('index.html', suggestion=commands, error=None)
            else:
                return render_template('index.html', suggestion=None, error=f"Failed to validate JSON structure\nAI raw: {commands}")
        except Exception as e:
            return render_template("index.html", suggestion=None, error=f"Failed to parse AI JSON: {e}\nAI raw: {command_suggestions}")
    return render_template('index.html', suggestion = None, error="Please enter instructions above")

# --- When user clicks "Execute command in docker" button
@app.route('/run', methods=['POST'])
def run():
    command = request.form['approved_cmd']
    if command:
        ok, reason = valid_command(command)
        if not ok:
            return render_template("index.html", suggestion=None, error=f"Command rejected: {reason}")
        # At this point, command is recognized as VALID by basic safety checks


        return render_template('index.html', instruction = False, error="VALID!")
    else:
        return render_template('index.html', instruction = False, error="No command selected to run")
    
# --- Main page ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', instruction = False)