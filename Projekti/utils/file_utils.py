import os, time, uuid, json
import ast

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

def write_json(session_output):
    """
    Write session output to a pretty-printed JSON file.
    Accepts dict/list, JSON string, or Python-literal string and normalizes to JSON.
    Returns the output filename.
    """
    # Normalize input into a Python object
    if isinstance(session_output, (dict, list)):
        data = session_output
    elif isinstance(session_output, str):
        s = session_output.strip()
        try:
            data = json.loads(s)  # valid JSON string
        except json.JSONDecodeError:
            try:
                data = ast.literal_eval(s)  # Python literal like "[{'a': 1}]"
            except Exception:
                data = {"raw": s}  # fallback: wrap raw string
    else:
        data = session_output

    filename = find_new_file_name("tool_output.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=False, default=str)
        f.write("\n")
    return filename