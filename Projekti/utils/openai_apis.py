from openai import OpenAI

client = OpenAI()

SUGGEST_PROMPT = """
You are a cybersecurity assistant. Translate this user request into a safe command that uses only nmap or nikto against a Docker target container address "poc_target", "localhost" or hostname "dvwa".
Never suggest a command that is directed towards other addresses.
Return JSON array of commands like:
[
  {"tool":"nmap", "command":"nmap -sV poc_target -p 80"}
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
"""
def ask_model(prompt, max_tokens=400):
    '''
    Ask model for a command suggestion
    '''
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
    '''
    Ask model for command output analysis
    '''
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
    
def conclusive_analysis(all_results, max_tokens=1000):
    '''
    Ask model conclusive analysis of command outputs
    '''
    # Build a single string; Responses API does not accept a list[str] for `input`
    prompt_text = "\n\n".join(str(result.get('stdout', '')) for result in all_results)
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