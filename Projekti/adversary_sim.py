import shlex
from flask import Flask, request, render_template
from openai_apis import ask_model
from checks import extract_json, validateStructure, valid_command
import subprocess

app = Flask(__name__)


def run_command(command: list[str]):
     # Convert "nmap -sV dvwa" -> ["nmap", "-sV", "dvwa"]
    args = shlex.split(command)

    print(f'Running command: {command} in docker container instrumentisto/nmap')
    result = subprocess.run(
        ["docker", "run", "--rm", "--network=projekti_pocnet", "instrumentisto/nmap"] + args,
        capture_output=True,
        text=True
    )
    print(result)
    return result.stdout
    
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
        print(run_command(command))

        return render_template('index.html', instruction = False, error="VALID!")
    else:
        return render_template('index.html', instruction = False, error="No command selected to run")
    
# --- Main page ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', instruction = False)