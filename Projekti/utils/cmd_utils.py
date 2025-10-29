"""
Utilities for validating and executing a restricted set of shell commands
inside a Docker executor container.

This module provides:
- is_valid_port: basic check for port range validity
- get_nmap_parser: create a parser for the nmap command
- get_nikto_parser: create a parser for the nikto command
- safe_command: basic safety checks for commands and targets
- validate_cmd: checks for duplicates and delegates to allowed_command
- run_command: executes a validated command inside a Docker container
- update_command: update a saved suggestion (1-based index)
- remove_cmd: remove a saved suggestion (1-based index)
"""

import shlex
import argparse
import subprocess
import re
from typing import Dict, List, Optional, Set, Tuple

ALLOWED_TOOLS: Set[str] = {"nmap", "nikto"}

# The 192.* addresses are the developer's PC and router.
ALLOWED_TARGETS: List[str] = [
    "dvwa",
    "http://dvwa:80",
    "192.168.88.1",
    "192.168.88.254",
    "172.20.0.0",
    "localhost",
    "127.0.0.1",
]

FORBIDDEN_CHARS: List[str] = [";", "&", "|", "`", "$(", ">", "<"]

ALLOWED_FLAGS: Dict[str, Set[str]] = {
    "nmap": {
        "-sT",
        "-sn",
        "-sV",
        "-sC",
        "-p",
        "-F",
        "-Pn",
        "-n",
        "-sL",
    },
    "nikto": {
        "-h",
        "-p",
    },
}


def is_valid_port(value):

    '''
    Checks if a port/port range is valid
    First checks if a port is a single valid port
    If not, creates regex and tries full match

    Args:
        value (str): port number or range
    
    Issues:
        Values like '50-30' or '10-5' still pass the regex. Would require more robust verification
    '''
    try:
        port = int(value)
        if 1 <= port <= 65535:
            return port
        else:
            raise argparse.ArgumentTypeError(
                f"{port} is not a valid port (1-65535)."
            )
        
    except ValueError:
        
        # Create regex for port validation
        port_atom = r"(6553[0-5]|655[0-2]\d|65[0-4]\d{2}|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3})"
        port_or_range = rf"{port_atom}(-{port_atom})?"
        port_list_regex = rf"^{port_or_range}(,{port_or_range})*$"
        PORT_VALIDATOR = re.compile(port_list_regex)

        if PORT_VALIDATOR.fullmatch(value):
            return value
            
        raise argparse.ArgumentTypeError(
            f"'{value}' is not a valid port or range."
        )

def get_nmap_parser():
    '''
    Creates parser for the nmap command
    Adds flags in ALLOWED_FLAGS as arguments
    '''
    parser = argparse.ArgumentParser(prog="nmap", add_help=False)

    # Flags that take no value (booleans)
    for flag in ALLOWED_FLAGS["nmap"]:
        if not flag == "-p":
            parser.add_argument(flag, action='store_true') # SYN scan
    
    # Flags that take a value
    parser.add_argument('-p', '--port', type=is_valid_port, dest='port')

    # 'nargs="*"' will collect all other arguments (like the target)
    parser.add_argument('targets', nargs='*')
    return parser


def get_nikto_parser():
    '''
    Creates parser for the nikto command
    Adds flags in ALLOWED_FLAGS as arguments
    '''
    parser = argparse.ArgumentParser(prog="nikto", add_help=False)
    # --- Whitelist of allowed flags ---
    parser.add_argument('-h', '--host', dest='host')
    parser.add_argument('-p', '--port', type=is_valid_port, dest='port')
    
    return parser

TOOL_PARSERS = {
    'nmap': get_nmap_parser(),
    'nikto': get_nikto_parser()
}


def safe_command(command: str) -> Tuple[bool, str]:
    """
    Determine whether a proposed shell command is safe to run.

    Checks performed:
    - command is non-empty and splits into arguments
    - the tool (first argument) is in ALLOWED_TOOLS
    - the command string does not contain any FORBIDDEN_CHARS
    - the command string only contains flags listed in ALLOWED_FLAGS
    - the command doesn't contain conflicting flags (that cause errors)
    - the port ranges in the command are valid
    - the specified target is in ALLOWED_TARGETS 
    - command structure is valid, no duplicate targets etc.

    Returns:
        (True, "") if the command is allowed,
        otherwise (False, reason).

    Please note that this check does not quarantee absolute command validity
    and safety. There might be some cases where an unsafe command might still pass through!
    """
    try:
        args = shlex.split(command)
        tool = args[0]
    except (IndexError, ValueError):
        return False, "Empty or invalid command"

    if tool not in ALLOWED_TOOLS:
        return False, f"Tool '{tool}' is not allowed."

    # Forbidden characters anywhere in the command string
    if any(ch in command for ch in FORBIDDEN_CHARS):
        return False, "Command contains forbidden characters"

    parser = TOOL_PARSERS[tool]

    try:
        # Parse the command
        known_args, unknown = parser.parse_known_args(args[1:])
        # Check for unallowed arguments
        if unknown:
            return False, f"Command contains unknown or invalid arguments: {unknown}"
        # Check for conflicting flags
        if hasattr(known_args, 'sn') and known_args.sn and any([
            getattr(known_args, 'sT', False),
            getattr(known_args, 'sC', False),
            getattr(known_args, 'sV', False)
        ]):
            return False, f"Command contains conflicting flags"
        # Check parsed targets and host fields
        targets_to_check = []
        if hasattr(known_args, 'targets'):
            targets_to_check.extend(known_args.targets)
        if hasattr(known_args, 'host'):
            targets_to_check.append(known_args.host)
        # If target is allowed, append to approved_targets
        approved_targets = []
        for target in ALLOWED_TARGETS:
            for t in targets_to_check:
                if target == t:  # Exact match
                    approved_targets.append(target)
        # If more or less than 1 target, return false
        if len(approved_targets) != 1:
            return False, "Command target not allowed"
        
    except argparse.ArgumentError as e:
        # This catches errors from our 'is_valid_port' function!
        return False, f"Invalid argument: {e}"
    except SystemExit:
        # Argparse calls sys.exit() on error
        return False, "Command has a formatting error."

    return True, ""


def validate_cmd(command: str, executed_commands: List[str]) -> Tuple[bool, str]:
    """
    Validate that a command is allowed and has not already been executed.

    Args:
        command: The command string to validate.
        executed_commands: List of previously executed command strings
                           in the current session.

    Returns:
        (True, "") if the command is valid and not repeated,
        otherwise (False, reason).
    """
    print(f"Validating command: {command}")
    if not command:
        return False, "No command selected to run"

    ok, reason = safe_command(command)

    if not ok:
        print(f"Error: {reason}\n")
        return False, f"Unsafe command: {reason}"
    
    if command in executed_commands:
        print("Command already executed in this session!\n")
        return False, "Command already executed in this session!"

    print("Valid command!\n")
    return True, ""


def run_command(EXECUTOR_CONTAINER: str, command: str) -> Optional[subprocess.CompletedProcess]:
    """
    Execute a command inside a Docker executor container.

    Args:
        EXECUTOR_CONTAINER: Name of the docker container where the command
                            will be executed.
        command: The command string that will be run inside the container.

    Returns:
        subprocess.CompletedProcess on success, or None on error.
    """
    args = shlex.split(command)
    print(f"Running command: {command} in docker container {EXECUTOR_CONTAINER}")

    try:
        result = subprocess.run(
            ["docker", "exec", EXECUTOR_CONTAINER] + args,
            capture_output=True,
            text=True,
        )
        return result
    except Exception as e:
        print(f"Error running command: {e}")
        return None


def update_command(
    suggestions: List[Dict[str, str]],
    index: Optional[str],
    cmd: Optional[str],
) -> Optional[List[Dict[str, str]]]:
    """
    Update a command suggestion in the session cache.

    The index is interpreted as a 1-based string index. If index or cmd is
    None or invalid, the function returns None.

    Args:
        suggestions: List of suggestion dicts (each typically contains
                     'tool' and 'command' keys).
        index: 1-based index string indicating which suggestion to update.
        cmd: New command string to store.

    Returns:
        The updated suggestions list on success, otherwise None.
    """
    if index is None or cmd is None:
        return None

    try:
        idx = int(index)
    except ValueError:
        print(f"Error updating command: invalid index '{index}'")
        return None

    if not (1 <= idx <= len(suggestions)):
        print(f"Error updating command: index {idx} out of range")
        return None

    try:
        print(f"Updating command at index {idx} to '{cmd}'")
        args = shlex.split(cmd)
        tool = args[0]
        print(f"Tool: {tool}, command: {cmd}")
        suggestions[idx - 1] = {"tool": tool, "command": cmd}
        print("Successfully updated session cache!\n")
        return suggestions
    except (IndexError, ValueError) as e:
        print(f"Error updating command: {e}")
        return None


def remove_cmd(
    suggestions: List[Dict[str, str]],
    index: Optional[str],
    cmd: Optional[str],
) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Remove a suggestion from the session cache.

    The index is interpreted as a 1-based string index. If removal succeeds,
    returns (True, updated_suggestions). On failure, returns (False, suggestions).

    Args:
        suggestions: List of suggestion dicts.
        index: 1-based index string indicating which suggestion to remove.
        cmd: Unused parameter kept for API compatibility.

    Returns:
        Tuple where first element indicates success, second element is the
        (possibly modified) suggestions list.
    """
    if index is None:
        print("Error removing command: index is None")
        return False, suggestions

    try:
        idx = int(index)
    except ValueError:
        print(f"Error removing command: invalid index '{index}'")
        return False, suggestions

    if not (1 <= idx <= len(suggestions)):
        print(f"Error removing command: index {idx} out of range")
        return False, suggestions

    try:
        print(f"Removing command at index {idx} from suggestions...")
        del suggestions[idx - 1]
        print("Successfully removed command!\n")
        return True, suggestions
    except (IndexError, ValueError) as e:
        print(f"Error removing command: {e}\n")
        return False, suggestions