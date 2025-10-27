"""
File utilities for managing tool outputs, session data, and report generation.

This module provides functions for:
- File name generation and conflict resolution
- JSON parsing and validation
- Session data persistence
- Markdown report generation
"""

import os
import time
import uuid
import json
import re
import ast
from mdutils import MdUtils

ALLOWED_TOOLS = {"nmap", "nikto"}


def find_new_file_name(base_name: str) -> str:
    """
    Find a new filename that doesn't already exist.
    
    Adds a numeric suffix to the base name if the file already exists,
    while preserving the file extension.

    Args:
        base_name: The base filename to use.

    Returns:
        A filename that doesn't exist in the current directory.
        
    Example:
        If 'output.json' exists, returns 'output_1.json'.
    """
    if not os.path.exists(base_name):
        return base_name

    i = 1
    while True:
        file_name, file_extension = os.path.splitext(base_name)
        new_name = f"{file_name}_{i}{file_extension}"
        if not os.path.exists(new_name):
            return new_name
        i += 1


def extract_json(text):
    """
    Extract and parse JSON from text input.
    
    Attempts multiple parsing strategies:
    1. Direct JSON parsing
    2. Regex extraction of JSON array
    
    Args:
        text: String containing JSON data.
        
    Returns:
        Parsed JSON object (dict or list).
        
    Raises:
        ValueError: If no valid JSON can be extracted.
    """
    try:
        return json.loads(text)
    except Exception:
        pass
    
    # Try to find first [...] block
    m = re.search(r'(\[.*\])', text, re.S)
    if m:
        candidate = m.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            pass
    
    raise ValueError("Could not parse JSON from model output")


def validateStructure(commands):
    """
    Validate the structure of command JSON.
    
    Ensures that:
    - Input is a list
    - Each item is a dict with 'command' and 'tool' keys
    - Tool names are in ALLOWED_TOOLS
    
    Args:
        commands: List of command dictionaries to validate.
        
    Returns:
        True if structure is valid, False otherwise.
    """
    if not isinstance(commands, list):
        return False
    
    for cmd in commands:
        if not isinstance(cmd, dict) or "command" not in cmd or "tool" not in cmd:
            return False
        if cmd.get("tool") not in ALLOWED_TOOLS:
            return False
    return True


def write_json(output):
    """
    Write session output to a pretty-printed JSON file.
    
    Normalizes various input formats (dict, list, JSON string, or Python
    literal) into a structured JSON file with session metadata.
    
    Args:
        output: Data to write. Can be dict, list, JSON string, or Python literal.
        
    Returns:
        The output filename.
    """
    # Normalize input into a Python object
    if isinstance(output, (dict, list)):
        data = output
    elif isinstance(output, str):
        s = output.strip()
        try:
            data = json.loads(s)  # Valid JSON string
        except json.JSONDecodeError:
            try:
                data = ast.literal_eval(s)  # Python literal like "[{'a': 1}]"
            except Exception:
                data = {"raw": s}  # Fallback: wrap raw string
    else:
        data = output

    output_json = {
        "session_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "entries": data
    }
    
    filename = find_new_file_name("tool_output.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=4, ensure_ascii=False,
                  sort_keys=False, default=str)
        f.write("\n")
    
    return filename


def save_result(temp_file, command, stdout, stderr, prompt_analysis):
    """
    Save command execution results to a temporary session file.
    
    Creates a new entry with command details, outputs, and AI analysis.
    Creates the file if it doesn't exist.
    
    Args:
        temp_file: Path to the temporary JSON file.
        command: The command that was executed.
        stdout: Standard output from the command.
        stderr: Standard error from the command.
        prompt_analysis: AI analysis of the command output.
    """
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "command": command,
        "stdout": stdout,
        "stderr": stderr,
        "prompt_analysis": prompt_analysis
    }
    
    try:
        # Create file if missing
        if not os.path.exists(temp_file):
            with open(temp_file, "w") as f:
                json.dump([], f)

        # Append entry
        with open(temp_file, "r+") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
            print("Results added to session memory!\n")
    except Exception as e:
        print(f"Error: saving output to a temporary file failed! {e}")


def get_analysis(temp_file):
    """
    Fetch the final analysis from the temporary file.
    
    Args:
        temp_file: Path to the temporary JSON file.
        
    Returns:
        The final analysis text if found, None otherwise.
    """
    all_results = load_results(temp_file)
    for entry in all_results:
        if "final_analysis" in entry:
            return entry["final_analysis"]
    return None


def save_analysis(temp_file, commands, final_analysis_text):
    """
    Save final analysis to the temporary file.
    
    Args:
        temp_file: Path to the temporary JSON file.
        commands: List of commands the analysis is based on.
        final_analysis_text: The analysis text to save.
    """
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "based_on": commands,
        "final_analysis": final_analysis_text
    }
    
    try:
        with open(temp_file, "r+") as f:
            data = json.load(f)
            if isinstance(data, list):
                data.append(entry)
            else:
                data[entry] = entry
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
    except Exception as e:
        print(f"Error: saving analysis failed: {e}")


def clean_temp(temp_file):
    """
    Clear the contents of the temporary file.
    
    Resets the file to an empty JSON array.
    
    Args:
        temp_file: Path to the temporary JSON file.
    """
    if os.path.exists(temp_file):
        with open(temp_file, "w") as f:
            json.dump([], f)


def load_results(temp_file):
    """
    Load all results from the temporary JSON file.
    
    Args:
        temp_file: Path to the temporary JSON file.
        
    Returns:
        List of result entries, or empty list if file doesn't exist.
    """
    if not os.path.exists(temp_file):
        return []
    with open(temp_file) as f:
        all_results = json.load(f)
        command_results = [result for result in all_results if "command" in result]
        return command_results


def write_md(results):
    """
    Generate a Markdown report from session results.
    
    Creates a formatted Markdown file with:
    - Command execution details
    - Command outputs
    - AI analysis
    - Final analysis summary
    
    Args:
        results: List of result entries from the session.
        
    Returns:
        The output Markdown filename.
    """
    filename = find_new_file_name("tool_output.md")
    md_file = MdUtils(file_name=filename, title='Tool output')

    for result in results:
        if "final_analysis" in result:
            md_file.new_header(level=1, title='Analysis results')
            md_file.new_paragraph(
                f'Based on commands: {result["based_on"]}',
                bold_italics_code="b"
            )
            md_file.new_paragraph(
                f'Timestamp: {result["timestamp"]}',
                bold_italics_code="b"
            )
            md_file.new_paragraph(
                f'ID: {result["id"]}',
                bold_italics_code="b"
            )
            md_file.new_header(level=2, title='Analysis output:')
            md_file.new_paragraph(result["final_analysis"])
        else:
            md_file.new_header(level=1, title='Command results')
            md_file.new_paragraph(
                f'Command: {result["command"]}',
                bold_italics_code="b"
            )
            md_file.new_paragraph(
                f'Timestamp: {result["timestamp"]}',
                bold_italics_code="b"
            )
            md_file.new_paragraph(
                f'ID: {result["id"]}',
                bold_italics_code="b"
            )
            if "stderr" not in result or not result["stderr"]:
                md_file.new_paragraph('Success!', bold_italics_code="b")
            else:
                md_file.new_paragraph(
                    f'{result["stderr"]}',
                    bold_italics_code="b"
                )
            md_file.new_header(level=2, title='Command output:')
            md_file.new_paragraph(result["stdout"])
            md_file.new_header(level=2, title='AI analysis:')
            md_file.new_paragraph(result["prompt_analysis"])

    md_file.create_md_file()
    return filename