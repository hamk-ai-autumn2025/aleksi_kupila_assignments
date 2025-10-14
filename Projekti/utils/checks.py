import json, shlex, re

ALLOWED_TOOLS = {"nmap", "nikto"}
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

# --- Basic command safety check ---
def valid_command(command):
    '''
    Checks if a command is "safe" to run in a local Docker container
    '''
    # The 192. addresses are my PC and router
    ALLOWED_TARGETS = ["dvwa", "192.168.88.1", "192.168.88.254", '172.20.0.0', "localhost", "127.0.0.1"]
    FORBIDDEN_CHARS = [";", "&", "|", "`", "$(", ">", "<"]
    ALLOWED_FLAGS = {
        "nmap": {"-sT", "-sn","-sV", "-sC", "-p", "-T4", "-F", "-Pn", "-n", "--top-ports", "--open", "--version-light", "-sL", "-r"},
        "nikto": {"-h", "-p", "-ssl", "-nossl", "-tls", "-timeout", "-nointeractive", "-Display", "-Plugins", "-url"}
    }
    try:
        args = shlex.split(command)
        tool = args[0]
        # Check if suggested tool is allowed
        if tool not in ALLOWED_TOOLS:
            return False, f"Tool '{tool}' is not allowed."
    except IndexError:
        return False, "Empty command"
    
    # Check all arguments (skipping the tool name itself)
    for arg in args[1:]:
        if arg.startswith("-"): # It's a flag
            if arg not in ALLOWED_FLAGS.get(tool, set()):
                return False, f"Flag '{arg}' is not allowed for {tool}."
    # If command contains dangerous characters
    if any(ch in command for ch in FORBIDDEN_CHARS):
        return False, "Command contains forbidden characters"

    # Check if target machine is an allowed target
    if not any(t in command for t in ALLOWED_TARGETS):
        return False, "Command target not allowed; must target local test containers"
    return True, ""