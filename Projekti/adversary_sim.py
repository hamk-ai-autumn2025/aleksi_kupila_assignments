"""
Adversary Simulator Flask Application

An AI-powered cybersecurity adversary simulator that suggests commands based on
natural language user input, executes them inside a sandboxed Docker container,
and analyzes the results using AI models.

This application provides a web interface for:
- Generating command suggestions from natural language instructions
- Validating and executing commands in a secure container environment
- Analyzing command outputs using AI
- Generating conclusive security analysis reports
- Saving session data in JSON or Markdown format
"""

from flask import Flask, request, render_template, session, jsonify
from flask_session import Session
from utils.ai_utils import ask_model, ask_analysis, conclusive_analysis
from utils.file_utils import (
    extract_json,
    validateStructure,
    write_json,
    save_result,
    save_analysis,
    clean_temp,
    get_entry,
    write_md
)
from utils.cmd_utils import (
    remove_cmd,
    run_command,
    update_command,
    validate_cmd
)

EXECUTOR_CONTAINER = "command_executor"
TEMP_FILE = "TEMP.json"
OUTPUT_DIR = "output"

app = Flask(__name__)

# Sessions expire when the browser is closed
app.config["SESSION_PERMANENT"] = False
# Store session data in files
app.config["SESSION_TYPE"] = "filesystem"

# Initialize Flask-Session
session = Session(app)
session.executed_commands = []
session.command_suggestions = []

# Clean temp file on startup
clean_temp(TEMP_FILE)


def render_partial(template_name, **context):
    """
    Render a Jinja template fragment and return it as JSON.

    Args:
        template_name (str): Name of the template file to render
        **context: Additional context variables to pass to the template

    Returns:
        flask.Response: JSON response containing the rendered HTML
    """
    analysis = get_entry(TEMP_FILE, "final_analysis")
    latest_analysis = None
    if analysis:
        latest_analysis = analysis[-1]["final_analysis"]  # Latest final analysis
    html = render_template(template_name, **context, analysis=latest_analysis)
    
    return jsonify({'html': html})


@app.route('/suggest', methods=['POST'])
def suggest():
    """
    Handle command suggestion requests.

    Processes natural language instructions and generates command suggestions
    using an AI model. Validates the JSON structure of AI responses.

    Returns:
        flask.Response: Rendered template with command suggestions or error message
    """
    instruction = request.form["instruction"]
    cmd_results = get_entry(TEMP_FILE, "command")

    if instruction:
        # Request LLM for a command
        command_suggestions = ask_model(instruction, 400)
        
        # If suggestion is EMPTY
        if command_suggestions == "[]":
            error_msg = (
                f"AI answer was empty. Maybe the prompt asked for a "
                f"forbidden command?\nAI raw: {command_suggestions}"
            )
            return render_partial(
                'answer.html',
                suggestion=None,
                results=cmd_results,
                error=error_msg
            )
        
        try:
            commands = extract_json(command_suggestions)
            
            if validateStructure(commands):
                session.command_suggestions = commands
                return render_partial(
                    'answer.html',
                    suggestion=commands,
                    results=cmd_results,
                    success="Commands generated!"
                )
            else:
                error_msg = (
                    f"Failed to validate JSON structure\n"
                    f"AI raw: {commands}"
                )
                return render_partial(
                    'answer.html',
                    suggestion=None,
                    results=cmd_results,
                    error=error_msg
                )
        except Exception as e:
            error_msg = (
                f"Failed to parse AI JSON: {e}\n"
                f"AI raw: {command_suggestions}"
            )
            return render_partial(
                "answer.html",
                suggestion=None,
                results=cmd_results,
                error=error_msg
            )
    
    print("Error: no instructions entered!\n")
    return render_partial(
        'answer.html',
        suggestion=None,
        results=cmd_results,
        error="Please enter instructions above"
    )


@app.route('/run', methods=['POST'])
def run():
    """
    Handle command execution and validation requests.

    Processes user actions including:
    - Removing command suggestions
    - Validating commands
    - Executing commands in the sandboxed container
    - Analyzing command outputs using AI

    Returns:
        flask.Response: Rendered template with execution results or error message
    """
    action = request.form.get('action')
    command_index = request.form.get('cmd_index')
    command = request.form[f"approved_cmd_{command_index}"]
    cmd_results = get_entry(TEMP_FILE, "command")

    # Handle remove button
    if action == 'remove_suggestion':
        ok, cmd_suggestions = remove_cmd(
            session.command_suggestions,
            command_index,
            command
        )
        if ok:
            return render_partial(
                "answer.html",
                suggestion=cmd_suggestions,
                results=cmd_results,
                success="Command suggestion removed!"
            )
        else:
            return render_partial(
                "answer.html",
                suggestion=cmd_suggestions,
                results=cmd_results,
                error="Command suggestion removal failed!"
            )

    print(f"Entered command {command} at index {command_index}")

    valid, reason = validate_cmd(command, session.executed_commands)
    if not valid:
        return render_partial(
            "answer.html",
            suggestion=session.command_suggestions,
            results=cmd_results,
            error=reason
        )
    
    # At this point, command is recognized as VALID by basic safety checks

    # Update session cache
    suggestions = update_command(
        session.command_suggestions,
        command_index,
        command
    )

    if action == 'validate':
        return render_partial(
            "answer.html",
            suggestion=session.command_suggestions,
            results=cmd_results,
            success="Valid command!"
        )

    command_output = run_command(EXECUTOR_CONTAINER, command)
    prompt_analysis = ask_analysis(command_output.stdout)
    session.executed_commands.append(command)
    
    if suggestions:
        session.command_suggestions = suggestions

    if command_output and prompt_analysis:
        save_result(
            TEMP_FILE,
            command,
            command_output.stdout,
            command_output.stderr,
            prompt_analysis
        )
        cmd_results = get_entry(TEMP_FILE, "command")
        return render_partial(
            'answer.html',
            suggestion=session.command_suggestions,
            results=cmd_results,
            success=f"Executed {command}"
        )
    else:
        return render_partial(
            'answer.html',
            suggestion=session.command_suggestions,
            results=cmd_results,
            error="Generating analysis failed"
        )


@app.route("/analysis", methods=["POST"])
def get_conclusive_analysis():
    """
    Generate and save a conclusive security analysis.

    Aggregates all command outputs and generates a comprehensive AI-powered
    security analysis of the entire session.

    Returns:
        flask.Response: Rendered template with success or error message
    """
    cmd_results = get_entry(TEMP_FILE, "command")
    
    try:
        # Extract command outputs from the results
        prompt_text = "\n\n".join(
            str(result.get('stdout', '')) for result in cmd_results
        )
        # Extract commands from the results
        commands = "\n".join(
            str(result.get('command', '')) for result in cmd_results
        )
        ai_analysis = conclusive_analysis(prompt_text)
        save_analysis(TEMP_FILE, commands, ai_analysis)
        return render_partial(
            'answer.html',
            suggestion=session.command_suggestions,
            results=cmd_results,
            success="Conclusive analysis generated!"
        )
    except Exception as e:
        print(f"Error: generating conclusive analysis failed: {e}")
        return render_partial(
            'answer.html',
            suggestion=session.command_suggestions,
            results=cmd_results,
            error="Failed to generate conclusive analysis!"
        )


@app.route('/save_json', methods=['POST'])
def save_json():
    """
    Save the current session data to a JSON file.

    Returns:
        flask.Response: Rendered template with success message
    """
    results = get_entry(TEMP_FILE, "id")
    cmd_results = get_entry(TEMP_FILE, "command")
    write_json(results, OUTPUT_DIR)
    return render_partial(
        'answer.html',
        suggestion=session.command_suggestions,
        results=cmd_results,
        success="Output saved!"
    )


@app.route('/save_md', methods=['POST'])
def save_md():
    """
    Save the current session data to a Markdown file.

    Returns:
        flask.Response: Rendered template with success message
    """
    results = get_entry(TEMP_FILE, "id")
    cmd_results = get_entry(TEMP_FILE, "command")
    write_md(results, OUTPUT_DIR)
    return render_partial(
        'answer.html',
        suggestion=session.command_suggestions,
        results=cmd_results,
        success="Output saved!"
    )


@app.route('/reset', methods=['POST'])
def reset():
    """
    Reset the application state.

    Clears the temporary file, executed commands history, and command
    suggestions from the session.

    Returns:
        flask.Response: Rendered index template
    """
    clean_temp(TEMP_FILE)
    session.executed_commands = []
    session.command_suggestions = []
    return render_template('index.html', instruction=False)


@app.route('/', methods=['GET'])
def index():
    """
    Render the main application page.

    Initializes a clean session by clearing the temporary file.

    Returns:
        flask.Response: Rendered index template
    """
    clean_temp(TEMP_FILE)
    return render_template('index.html', instruction=False)
