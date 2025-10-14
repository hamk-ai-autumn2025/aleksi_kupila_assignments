import os
from openai import OpenAI

api_key=os.environ['OPENROUTER_API_KEY']
if not api_key:
    raise ValueError("OpenRouter API key not found. Please set OPENROUTER_API_KEY in your .env file.")

client = OpenAI(

  base_url="https://openrouter.ai/api/v1",

  api_key=api_key,

)
def call_openrouter_api(messages, model):

    print(f"Fetching API response from {model}...")
    try:
        response = client.chat.completions.create(
            model=model,  # You can change this to any supported model
            messages=messages
        )
    except Exception as e:
        print(f"Error fetching API response: {e}")
        return None
    return response.choices[0].message.content