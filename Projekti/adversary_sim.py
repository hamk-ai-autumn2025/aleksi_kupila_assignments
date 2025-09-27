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
        return render_template('index.html', instruction = instruction)
    else:
        return render_template('index.html', instruction = "Please enter instruction")

def valid_command(command):
    return None