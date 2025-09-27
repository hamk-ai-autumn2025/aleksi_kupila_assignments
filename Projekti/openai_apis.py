from openai import OpenAI

client = OpenAI()

SUGGEST_PROMPT = """
You are a cybersecurity assistant. Translate this user request into a safe command that uses only nmap or nikto against a Docker target container address "poc_target" or hostname "poc_target".
Return JSON array of commands like:
[
  {"tool":"nmap", "command":"nmap -sV poc_target -p 80"}
]
Only suggest safe scanning commands (no OS exploits, no file writes). For ports use -p flag if needed.
User request: {request}
"""

ANALYZE_PROMPT = """
You are a cybersecurity analyst. Analyze the following tool output and:
1) Summarize findings.
2) List severity: High/Medium/Low for each issue mentioned.
3) Suggest concrete mitigations.
Return a concise bullet list.
Tool output:
{output}
"""

def ask_model(prompt, max_tokens=400):
    resp = client.responses.create(
        model="gpt-4.1-mini",
        instructions=SUGGEST_PROMPT,
        input=prompt,
        temperature=0.0,
        max_output_tokens=max_tokens
    )
    print(resp.output_text)
    return resp.output_text