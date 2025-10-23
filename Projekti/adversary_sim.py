import shlex
from flask import Flask, request, render_template,  session, jsonify
from flask_session import Session
from utils.openai_apis import ask_model, ask_analysis, conclusive_analysis
from utils.file_utils import extract_json, validateStructure
from utils.cmd_utils import valid_command, remove_cmd, run_command
from utils.file_utils import write_json, save_result, load_results, save_analysis, clean_temp, get_analysis

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
    analysis = get_analysis(TEMP_FILE)
    html = render_template(template_name, **context, analysis = analysis)
    
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

def validate_cmd():
    print("Validating command...")
    return None

def update_command(index, cmd):
    suggestions = session.command_suggestions
    #print(suggestions)
    if index is not None and cmd is not None:
        try:
            index = int(index)
            if 0 <= index < len(suggestions):

                print(f"Updating command at index {index} to '{cmd}'")
                args = shlex.split(cmd)
                tool = args[0]
                print(f'Tool: {tool}, command: {cmd}')
                suggestions[index-1] = {'tool':tool,'command':cmd}
                session.command_suggestions = suggestions
                print("Succesfully updated session cache!\n")
                #print(session.command_suggestions)

        except (ValueError, IndexError) as e:
            # Handle cases where index is invalid
            print(f"Error updating command: {e}")

# --- When user clicks "Execute selected command" or "Edit selected command" button ---
@app.route('/run', methods=['POST'])
def run():
    action = request.form.get('action')
    #print(request.form)
    # Get command index
    command_index = request.form.get('cmd_index')
    # Get command tied to the index
    command = request.form[f"approved_cmd_{command_index}"]

    # Handle validate and remove buttons
    if action == 'validate':
        validate_cmd()
    if action == 'remove':
        remove_cmd()

    print(f"User tried executing command {command} at index {command_index}\n")

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
        # Update session cache
        update_command(command_index, command)

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
        return render_partial('answer.html', suggestion = session.command_suggestions, results = all_results, success = "Conclusive analysis generated!")
    
    except Exception as e:
        print(f"Error: generating conclusive analysis failed: {e}")
        return render_partial('answer.html', suggestion = session.command_suggestions, results = all_results, error=f"Failed to generate conclusive analysis!")


# --- When user clicks "Save session (JSON)" button
@app.route('/save', methods=['POST'])
def save_output():
    all_results = load_results(TEMP_FILE)
    write_json(all_results)
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
