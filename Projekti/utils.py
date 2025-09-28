import os, time, uuid, json

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

def write_json(command, output, analysis):
    '''
    Write nmap command output to a json file
    '''
    filename = find_new_file_name("tool_output.json")
    record = {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "command": command,
        "stdout": output,
        "stderr": "",
        "exit_code": None,
        'ai_analysis': analysis
    }
    with open(filename, 'w') as f:
        json.dump(record, f, indent=4, ensure_ascii=False)