import shlex, subprocess

ALLOWED_TOOLS = {"nmap", "nikto"}
# --- Basic command safety check ---
def allowed_command(command):
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
        print(f"Validating command: {command}")
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
    # If command contains forbidden characters
    if any(ch in command for ch in FORBIDDEN_CHARS):
        return False, "Command contains forbidden characters"

    # Check if target machine is an allowed target
    for target in ALLOWED_TARGETS:
        for argument in args:
            if argument == target:
                print("Valid command!\n\n")
                return True, ""
    return False, "Command target not allowed; must target local test containers"

    # Old insecure version
    #if not any(t in command for t in ALLOWED_TARGETS):
        #return False, "Command target not allowed; must target local test containers"
    #return True, ""

def validate_cmd(command, executed_commands):
    '''
    Function to check if a command is valid and is not already executed in the current session
    '''
    print("Validating command...")
    if command:
        ok, reason = allowed_command(command)

        if command in executed_commands:
            return False, "Command already executed in this session!"
        if not ok:
            return False, f"Command rejected: {reason}"
        return True, ""
    else:
        return False, "No command selected to run"
    
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
        # print(result)
        return result
    
    except Exception as e:
        print(f"Error running command: {e}")
        return None
    
def update_command(suggestions, index, cmd):

    #print(suggestions)
    if index is not None and cmd is not None:
        try:
            index = int(index)
            if 0 <= index < len(suggestions):

                print(f"Updating command at index {index} to '{cmd}'")
                args = shlex.split(cmd)
                tool = args[0]
                print(f'Tool: {tool}, command: {cmd}')
                suggestions[index-1] = {'tool':tool,'command':cmd}

                print("Succesfully updated session cache!\n")
                return suggestions
                #print(session.command_suggestions)

        except (ValueError, IndexError) as e:
            # Handle cases where index is invalid
            print(f"Error updating command: {e}")
            return None

def remove_cmd():
    print("Validating command...")
    return None