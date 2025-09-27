from flask import Flask, request, url_for, render_template
from markupsafe import escape
from openai_apis import ask_model

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', instruction = False)

@app.route('/suggest', methods=['POST'])
def suggest():
    instruction = request.form["instruction"]
    if instruction:
        command_suggestion = ask_model(instruction, 400)
        return render_template('index.html', suggestion = command_suggestion)
    else:
        return render_template('index.html', suggestion = "Please enter instruction")

def valid_command(command):
    return None