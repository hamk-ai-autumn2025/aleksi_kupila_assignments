import os, json
from flask import Flask, request, render_template,  session, jsonify
from flask_session import Session
from utils.openai_apis import ask_model, ask_analysis, conclusive_analysis
from utils.checks import extract_json, validateStructure, valid_command
from utils.file_utils import write_json, save_result, load_results, run_command, save_analysis, clean_temp

EXECUTOR_CONTAINER = "command_executor"
TEMP_FILE = "TEMP.json"

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False     # Sessions expire when the browser is closed
app.config["SESSION_TYPE"] = "filesystem"     # Store session data in files

# Initialize Flask-Session
session = Session(app)
session.executed_commands = []
session.command_suggestions = []

# Clean temp file
clean_temp(TEMP_FILE)

def render_partial(template_name, **context):
    """Render a Jinja template fragment and return it as JSON."""
    html = render_template(template_name, **context)
    return jsonify({'html': html})

# --- When user clicks "Get command suggestion" button
@app.route('/suggest', methods=['POST'])
def suggest():
    instruction = request.form["instruction"]
    all_results = load_results(TEMP_FILE)

    if instruction:
        # Request LLM for a command
        command_suggestions = ask_model(instruction, 400)
        # If suggestion is EMPTY
        if command_suggestions == "[]":
            return render_partial('answer.html', suggestion=None, results = all_results, error=f"AI answer was empty. Maybe the prompt asked for a forbidden command?\nAI raw: {command_suggestions}")
        try:
            commands = extract_json(command_suggestions)  # Try extracting JSON 
            if validateStructure(commands):  # If JSON structure is valid
                session.command_suggestions = commands
                return render_partial('answer.html', suggestion=commands, results = all_results, success=f"Commands generated!")
            else:
                return render_partial('answer.html', suggestion=None, results = all_results, error=f"Failed to validate JSON structure\nAI raw: {commands}")
        except Exception as e:
            return render_partial("answer.html", suggestion=None, results = all_results, error=f"Failed to parse AI JSON: {e}\nAI raw: {command_suggestions}")
    return render_partial('answer.html', suggestion = None, results = all_results, error="Please enter instructions above")

# --- When user clicks "Execute command in docker" button
@app.route('/run', methods=['POST'])
def run():
    command = request.form['approved_cmd']
    all_results = load_results(TEMP_FILE)

    if command:
        ok, reason = valid_command(command)

        if command in session.executed_commands:
            return render_partial("answer.html", suggestion = session.command_suggestions, results = all_results, error=f"Command already executed in this session!:")
        
        if not ok:
            return render_partial("answer.html", suggestion = session.command_suggestions, results = all_results, error=f"Command rejected: {reason}")
        
        # At this point, command is recognized as VALID by basic safety checks
        command_output = (run_command(EXECUTOR_CONTAINER, command))
        prompt_analysis = ask_analysis(command_output.stdout)
        session.executed_commands.append(command)
        if command_output and prompt_analysis:
            save_result(TEMP_FILE, command, command_output.stdout, command_output.stderr, prompt_analysis)
            all_results = load_results(TEMP_FILE)
            return render_partial('answer.html', suggestion = session.command_suggestions, results = all_results, success=f"Executed {command}")
        else: 
            return render_partial('answer.html', suggestion = session.command_suggestions, results = all_results, error="Generating analysis failed")

    else:
        return render_partial('answer.html', suggestion = session.command_suggestions, results = all_results, error="No command selected to run")


# ... When user clicks "Get conclusive analysis" button
@app.route("/analysis", methods=["POST"])
def get_conclusive_analysis():
    try:
        all_results = load_results(TEMP_FILE)
        ai_analysis = conclusive_analysis(all_results)
        save_analysis(TEMP_FILE, ai_analysis)
        return render_partial('answer.html', suggestion = session.command_suggestions, results = all_results, analysis=ai_analysis, success = "Conclusive analysis generated!")
    
    except Exception as e:
        print(f"Error: generating conclusive analysis failed: {e}")
        return render_partial('answer.html', suggestion = session.command_suggestions, results = all_results, error=f"Failed to generate conclusive analysis!")


# --- When user clicks "Save session (JSON)" button
@app.route('/save', methods=['POST'])
def save_output():
    all_results = load_results(TEMP_FILE)
    write_json(all_results)
    analysis = None
    # Get the final analysis from the json
    for entry in all_results:
        if "final_analysis" in entry:
            analysis = entry["final_analysis"]
            break 
    if analysis:
        return render_partial('answer.html', suggestion = session.command_suggestions, results = all_results, analysis = analysis, success="Output saved!")
    else:
        return render_partial('answer.html', suggestion = session.command_suggestions, results = all_results, success="Output saved!")

# --- Resets page, temp file and session storage ---
@app.route('/reset', methods=['POST'])
def reset():
    clean_temp(TEMP_FILE)
    session.executed_commands = []
    session.command_suggestions = []
    return render_template('index.html', instruction = False)

# --- Main page, resets temp file ---
@app.route('/', methods=['GET'])
def index():
    clean_temp(TEMP_FILE)
    return render_template('index.html', instruction = False)
