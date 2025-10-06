import shlex, subprocess
from flask import Flask, request, render_template
from openai_apis import ask_model, ask_analysis
from checks import extract_json, validateStructure, valid_command
from utils import write_json

EXECUTOR_CONTAINER = "command_executor"
app = Flask(__name__)

# --- Runs command inside a docker container
def run_command(command: list[str]):
     # Convert "nmap -sV dvwa" -> ["nmap", "-sV", "dvwa"]
    args = shlex.split(command)

    print(f'Running command: {command} in docker container projekti-executor')

    try:
        result = subprocess.run(
            ["docker", "exec", EXECUTOR_CONTAINER, "sudo"] + args,
            capture_output=True,
            text=True
        )
    except Exception as e:
        print(f"Error running command: {e}")
    return result
    
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
        command_output = (run_command(command))
        ai_analysis = ask_analysis(command_output.stdout)
        print(command_output.stdout)
        print(ai_analysis)

        return render_template('index.html', command=command, command_output = command_output.stdout, ai_analysis = ai_analysis, error="Success!")
    else:
        return render_template('index.html', suggestion = False, error="No command selected to run")
    
# --- When user clicks "Save output (JSON)" button
@app.route('/save', methods = ['POST'])
def save_output():
    command = request.form.get('command')
    raw_output = request.form['command_output']
    analysis = request.form['ai_analysis']
    write_json(command, raw_output, analysis)
    return render_template('index.html', error="Output saved!")
# --- Main page ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', instruction = False)