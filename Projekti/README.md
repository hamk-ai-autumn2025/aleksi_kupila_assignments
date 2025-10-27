[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](#license)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)]
[![Docker](https://img.shields.io/badge/docker-required-yellow.svg)]

# AI-powered vulnerability scanner

An AI-powered cybersecurity adversary simulator that suggests commands based on
natural language user input, executes them inside a sandboxed Docker container,
and analyzes the results using AI models.

---

## Features

- Generating command suggestions from natural language instructions
- Validating and executing commands in a secure container environment
- Analyzing command outputs using AI
- Generating conclusive security analysis reports
- Saving session data in JSON or Markdown format
- Written in Python, Flask and Jinja

---

## How it works

1. Client (web UI) → user provides a natural-language instruction.
2. AI model suggests one or more shell commands.
3. Commands are passed to a validation/safety layer (regex/whitelist / heuristic checks).
4. Approved commands are executed in a sandboxed Docker container.
5. Outputs are captured and sent back to AI for analysis and final report generation.
6. Session results can be exported to `.json` or `.md`.

---

## Prerequisites

1. **Software**
    Docker and Docker compose must be installed and running
    You can check this by running:
    ```bash
    docker ps
    ```

2. **Linux**
    Ensure your user is in the docker group so Docker commands can be run without sudo:
    You can achieve this by adding your user to the docker group:
    ```bash
    sudo usermod -aG docker $USER
    ```

3. **Windows**
    If you’re using Docker Desktop, no extra configuration is usually required.

---

## Configuration

- This application requires a valid OpenAI API key.
- The key can be either in your shell configuration (e.g. bash) or in an environmental file

You can create the environmental file as follows:

1. **Copy `.env.example` to `.env`**
    ```bash
    cp .env.example .env
    ```
2. **Edit `.env` and set your API key:**
    ```bash
    AI_API_KEY=your_key_here
    ```
Note that running the program by 'flask run' also needs environmental variable FLASK_APP configured (included in .env.example)

---

## Setup

1. **Create and activate a virtual environment**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
3. **Start docker environment (new terminal window)**
    ```bash
    docker compose up
    ```
4. **Start the application**
    ```bash
    flask run
    ```

---

## Usage

- Visit 'localhost:5000'
- Enter an instruction for AI in natural language, for example "Check open ports of DVWA"
- Validate and execute command. You can also edit, remove or just validate commands at this stage.
- You can view the scan results and analysis in the dropdown menu.
- You can generate a final analysis based on one or multiple command outputs.
- You can also save the session data in either .json or .md format.
- The page can be reset from the button in top right.

---

## 🔒 Security & Safety Notice

**Recommendations:**

This application is for educational/research use *only* in a controlled environment. It executes shell commands inside Docker containers and implements multiple safety layers, but **cannot** eliminate all risk. Misconfiguration (e.g., mounting Docker socket or running containers as privileged) may expose your host.

- Run the application only on your local machine or within a private test network.
- Never connect the application to the public internet or run commands against external targets without explicit authorization.
- Review Docker configurations and limit container privileges (e.g., avoid --privileged mode).
- The app does not guarantee absolute safety — specially crafted commands could still escape the container if Docker is misconfigured.
- Do not mount host sockets (e.g., `/var/run/docker.sock`) into the container.

**Disclaimer:**
The authors are not responsible for any damage, misuse, or legal consequences resulting from improper use of this software. Use responsibly and ethically.

**Intended use**
This tool was created as part of an AI project to demonstrate AI-assisted command execution and analysis within a sandboxed environment.