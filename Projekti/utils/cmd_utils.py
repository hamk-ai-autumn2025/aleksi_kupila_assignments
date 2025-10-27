"""
Utilities for validating and executing a restricted set of shell commands
inside a Docker executor container.

This module provides:
- allowed_command: basic safety checks for commands and targets
- validate_cmd: checks for duplicates and delegates to allowed_command
- run_command: executes a validated command inside a Docker container
- update_command: update a saved suggestion (1-based index)
- remove_cmd: remove a saved suggestion (1-based index)
"""

import shlex
import subprocess
from typing import Dict, List, Optional, Set, Tuple

ALLOWED_TOOLS: Set[str] = {"nmap", "nikto"}

# The 192.* addresses are the developer's PC and router.
ALLOWED_TARGETS: List[str] = [
    "dvwa",
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
        "-T4",
        "-F",
        "-Pn",
        "-n",
        "--top-ports",
        "--open",
        "--version-light",
        "-sL",
        "-r",
    },
    "nikto": {
        "-h",
        "-p",
        "-ssl",
        "-nossl",
        "-tls",
        "-timeout",
        "-nointeractive",
        "-Display",
        "-Plugins",
        "-url",
    },
}


def allowed_command(command: str) -> Tuple[bool, str]:
    """
    Determine whether a proposed shell command is permitted.

    Checks performed:
    - command is non-empty and splits into arguments
    - the tool (first argument) is in ALLOWED_TOOLS
    - flags (arguments starting with '-') are in ALLOWED_FLAGS for the tool
    - the command string does not contain any FORBIDDEN_CHARS
    - one of the ALLOWED_TARGETS appears as an argument

    Returns:
        (True, "") if the command is allowed,
        otherwise (False, reason).
    """
    try:
        print(f"Validating command: {command}")
        args = shlex.split(command)
        tool = args[0]
    except (IndexError, ValueError):
        return False, "Empty or invalid command"

    if tool not in ALLOWED_TOOLS:
        return False, f"Tool '{tool}' is not allowed."

    # Check flags
    for arg in args[1:]:
        if arg.startswith("-"):
            if arg not in ALLOWED_FLAGS.get(tool, set()):
                return False, f"Flag '{arg}' is not allowed for {tool}."

    # Forbidden characters anywhere in the command string
    if any(ch in command for ch in FORBIDDEN_CHARS):
        return False, "Command contains forbidden characters"

    # Check for an allowed target in the argument list
    for argument in args:
        if argument in ALLOWED_TARGETS:
            print("Valid command!\n")
            return True, ""

    return False, "Command target not allowed; must target local test containers"


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
    if not command:
        return False, "No command selected to run"

    ok, reason = allowed_command(command)
    if command in executed_commands:
        return False, "Command already executed in this session!"
    if not ok:
        return False, f"Command rejected: {reason}"
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