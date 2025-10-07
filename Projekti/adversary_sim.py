import shlex, subprocess, uuid, time
from flask import Flask, request, render_template,  session
from flask_session import Session
from utils.openai_apis import ask_model, ask_analysis, conclusive_analysis
from utils.checks import extract_json, validateStructure, valid_command
from utils.file_utils import write_json

EXECUTOR_CONTAINER = "command_executor"
TEMP_FILE = "temp"

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False     # Sessions expire when the browser is closed
app.config["SESSION_TYPE"] = "filesystem"     # Store session data in files

# Initialize Flask-Session
session = Session(app)
session.results = []
# --- Runs command inside a docker container
def run_command(command: list[str]):
     # Convert "nmap -sV dvwa" -> ["nmap", "-sV", "dvwa"]
    args = shlex.split(command)

    print(f'Running command: {command} in docker container projekti-executor')

    try:
        result = subprocess.run(
            ["docker", "exec", EXECUTOR_CONTAINER] + args,
            capture_output=True,
            text=True
        )
        print(result)
        return result
    
    except Exception as e:
        print(f"Error running command: {e}")
        return None

def add_result(command, command_output, prompt_analysis):
        
    session.results.append({
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "command": command,
        "stdout": command_output.stdout,
        "stderr": command_output.stderr,
        "ai_analysis": prompt_analysis
    })
    print("Results added to session memory!\n")    


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
                session.commands = commands
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
            return render_template("index.html", error=f"Command rejected: {reason}")
        # At this point, command is recognized as VALID by basic safety checks
        command_output = (run_command(command))
        prompt_analysis = ask_analysis(command_output.stdout)
        #print(command_output.stdout)
        #print(prompt_analysis)
        if command_output and prompt_analysis:
            add_result(command, command_output, prompt_analysis)
            return render_template('index.html', suggestion = session.commands, command=command, command_output = command_output.stdout, prompt_analysis = prompt_analysis, error="Success!")
        else: 
            return render_template('index.html', error="Generating analysis failed")

    else:
        return render_template('index.html', error="No command selected to run")


# ... When user clicks "Get conclusive analysis" button
@app.route("/analyze", methods=["POST"])
def get_conclusive_analysis():
    try:
        all_outputs = session["commands"]
        ai_analysis = conclusive_analysis(all_outputs)
        return render_template('index.html', conclusive_analysis=ai_analysis, error=None)
    
    except Exception as e:
        print(f"Error: generating conclusive analysis failed: {e}")
        return render_template('index.html', suggestion=None, error=f"Failed to generate conclusive analysis\nAI raw: {ai_analysis}")


# --- When user clicks "Save session (JSON)" button
@app.route('/save', methods=['POST'])
def save_output():
    session_output = f"{session.results}"
    write_json(session_output)
    return render_template('index.html', error="Output saved!")
# --- Main page ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', instruction = False)