"""
AI utility functions for cybersecurity command suggestions and analysis.

This module provides functions to interact with OpenAI's API for generating
security scanning commands and analyzing their outputs.
"""

from openai import OpenAI

client = OpenAI()

SUGGEST_PROMPT = """
You are a cybersecurity assistant. Translate this user request into a safe command that uses only nmap or nikto against a Docker target container address "dvwa", "localhost", 172.20.0.0 or 127.0.0.1.
Never suggest a command that is directed towards other addresses.
Return JSON array of commands like:
[
  {"tool":"nmap", "command":"nmap -p 1-80 dvwa"}
]
Only suggest safe scanning commands (no OS exploits, no file writes). For ports use -p flag if needed.
"""

ANALYZE_PROMPT = """
You are a cybersecurity analyst. Analyze the following tool output and:
1) Summarize findings.
2) List severity: High/Medium/Low for each issue mentioned.
3) Suggest concrete mitigations.
Return a concise bullet list.
"""

CONCLUDE_PROMPT = """
Analyze the outputs of these commands and provide a conclusive summary of the target's security posture. 
Focus on key vulnerabilities, patterns, and recommendations. 
Do not repeat the outputs; summarize them concisely.
Start by mentioning which commands the analysis is based on.
"""


def ask_model(prompt, max_tokens=400):
    """
    Request a command suggestion from the AI model.

    Args:
        prompt (str): The user's request for a security command.
        max_tokens (int, optional): Maximum tokens for the response. Defaults to 400.

    Returns:
        str: The AI-generated command suggestion, or None if an error occurs.
    """
    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            instructions=SUGGEST_PROMPT,
            input=prompt,
            temperature=0.0,
            max_output_tokens=max_tokens
        )
        print(resp.output_text)
        return resp.output_text

    except Exception as e:
        print(f"Error generating suggestion: {e}")
        return None


def ask_analysis(prompt, max_tokens=400):
    """
    Request an analysis of command output from the AI model.

    Args:
        prompt (str): The command output to be analyzed.
        max_tokens (int, optional): Maximum tokens for the response. Defaults to 400.

    Returns:
        str: The AI-generated analysis, or None if an error occurs.
    """
    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            instructions=ANALYZE_PROMPT,
            input=prompt,
            temperature=0.0,
            max_output_tokens=max_tokens
        )
        print(resp.output_text)
        return resp.output_text

    except Exception as e:
        print(f"Error generating analysis: {e}")
        return None


def conclusive_analysis(prompt_text, max_tokens=1000):
    """
    Request a conclusive analysis of multiple command outputs from the AI model.

    Args:
        prompt_text (str): The combined command outputs to be analyzed.
        max_tokens (int, optional): Maximum tokens for the response. Defaults to 1000.

    Returns:
        str: The AI-generated conclusive analysis, or None if an error occurs.
    """
    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            instructions=CONCLUDE_PROMPT,
            input=prompt_text,
            temperature=0.0,
            max_output_tokens=max_tokens
        )
        print(resp.output_text)
        return resp.output_text

    except Exception as e:
        print(f"Error generating analysis: {e}")
        return None