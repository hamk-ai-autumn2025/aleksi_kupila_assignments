import os, time, uuid, json, re, ast

ALLOWED_TOOLS = {"nmap", "nikto"}

def find_new_file_name(base_name: str) -> str:
    """
    Finds a new filename that doesn't already exist by adding a number to the end of the base name.
    Retains the file extension.

    Args:
        base_name (str): The base name to use.

    Returns:
        str: A new filename that doesn't already exist.
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

# --- Extract JSON file from AI output ---
def extract_json(text):
    '''
    Extracts JSON from str input
    '''
    try:
        return json.loads(text)
    except Exception:
        pass
    # try to find first [...] block
    m = re.search(r'(\[.*\])', text, re.S)
    if m:
        candidate = m.group(1)
        # try json
        try:
            return json.loads(candidate)
        except Exception:
            pass
    # give up
    raise ValueError("Could not parse JSON from model output")

# --- Validate JSON file structure ---
def validateStructure(commands):
    '''
    Checks JSON file structure integrity
    '''
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
    Accepts dict/list, JSON string, or Python-literal string and normalizes to JSON.
    Returns the output filename.
    """
    # Normalize input into a Python object
    if isinstance(output, (dict, list)):
        data = output
    elif isinstance(output, str):
        s = output.strip()
        try:
            data = json.loads(s)  # valid JSON string
        except json.JSONDecodeError:
            try:
                data = ast.literal_eval(s)  # Python literal like "[{'a': 1}]"
            except Exception:
                data = {"raw": s}  # fallback: wrap raw string
    else:
        data = output

    output_json = {
        "session_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "entries": data
    }
    filename = find_new_file_name("tool_output.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=4, ensure_ascii=False, sort_keys=False, default=str)
        f.write("\n")
    return filename

def save_result(TEMP_FILE, command, stdout, stderr, prompt_analysis):
    '''
    Save session records to a temporary file
    '''
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
        if not os.path.exists(TEMP_FILE):
            with open(TEMP_FILE, "w") as f:
                json.dump([], f)

        # Append entry
        with open(TEMP_FILE, "r+") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
            print("Results added to session memory!\n")
    except Exception as e:
        print(f"Error: saving output to a temporary file failed! {e}")

def get_analysis(TEMP_FILE):
    """
    Fetches final analysis from temp file, otherwise returns none
    """
    all_results = load_results(TEMP_FILE)
    for entry in all_results:
        if "final_analysis" in entry:
            analysis = entry["final_analysis"]
            return analysis
    return None

def save_analysis(TEMP_FILE, commands, final_analysis_text):
    '''
    Save final analysis on a file
    '''
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "based_on": commands,
        "final_analysis": final_analysis_text
    }
    try:
        with open(TEMP_FILE, "r+") as f:
            data = json.load(f)
            # If the file is a list of entries, append a separate final analysis record
            if isinstance(data, list):
                data.append(entry)
            else:
                data[entry] = entry
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
    except Exception as e:
        print(f"Error: saving analysis failed: {e}")

def clean_temp(TEMP_FILE):
    '''
    Cleans temporary file
    Takes temp file name as argument
    '''
    if os.path.exists(TEMP_FILE):
        with open(TEMP_FILE, "w") as f:
            json.dump([], f)

def load_results(TEMP_FILE):
    '''
    Load results from the temporary json file and return
    Takes temp file name as argument
    '''
    if not os.path.exists(TEMP_FILE):
        return []
    with open(TEMP_FILE) as f:
        return json.load(f)