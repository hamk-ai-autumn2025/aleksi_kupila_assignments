import os, time, uuid, json
import ast, subprocess, shlex


# --- Runs command inside a docker container
def run_command(EXECUTOR_CONTAINER, command: list[str]):
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

    filename = find_new_file_name("tool_output.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=False, default=str)
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

def save_analysis(TEMP_FILE, final_analysis_text):
    '''
    Save final analysis on a file
    '''
    try:
        with open(TEMP_FILE, "r+") as f:
            data = json.load(f)
            # If the file is a list of entries, append a separate final analysis record
            if isinstance(data, list):
                data.append({"final_analysis": final_analysis_text})
            else:
                data["final_analysis"] = final_analysis_text
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
    except Exception as e:
        print(f"Error: saving analysis failed: {e}")


def load_results(TEMP_FILE):
    '''
    Load results from the temporary json file and return
    '''
    if not os.path.exists(TEMP_FILE):
        return []
    with open(TEMP_FILE) as f:
        return json.load(f)