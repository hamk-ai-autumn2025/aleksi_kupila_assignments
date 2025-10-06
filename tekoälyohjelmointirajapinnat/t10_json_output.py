from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
import json, re

MODEL_NAME = "gpt-4.1-mini"
SYSTEM_PROMPT = """
    You are a dictionary specialist who knows the meaning of every word in every language.
    Your job is to provide a short definition, synonyms, antonyms, and 2-3 example sentences for the user's word.
    You must always respond in a structured JSON format. Do not output anything else.
    The JSON object must conform to the following schema:
    {
        "word": "string",
        "definition": "string",
        "synonyms": ["string"],
        "antonyms": ["string"],
        "examples": ["string", "string"]
    }
    Never output anything but strict json
    """

client = OpenAI()

def ask_model(prompt, max_tokens=400):
    '''
    Ask model word explanation in JSON format
    '''
    try:
        resp = client.responses.create(
            model=MODEL_NAME,
            instructions=SYSTEM_PROMPT,
            input=prompt,
            temperature=0.0,
            max_output_tokens=max_tokens
        )

        json_string = extract_json_from_response(resp.output_text)
        print(f"Output: {json_string}")

        if not json_string:
            print(f"\nValidation Error: No valid JSON object found in the model's response.\n")
            return None

        return WordDefinition.model_validate_json(json_string)
    
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"\nValidation Error: The model's response was not valid JSON or did not match the required structure.\nDetails: {e}\n")
        print(f"Raw response: {resp.output_text}")
        return None
    except Exception as e:
        print(f"\nAPI Error: Failed to generate response.\nDetails: {e}\n")
        return None

def extract_json_from_response(text: str) -> Optional[str]:
    """
    Finds and extracts a JSON object from a string that might be wrapped
    in markdown code blocks or have other text.
    """

    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return None

class WordDefinition(BaseModel):
    word: str = Field(..., min_length=1, description="The word being defined.")
    definition: str = Field(..., min_length=1, description="The definition of the word.")
    synonyms: List[str] = Field(default=[], description="A list of synonyms.")
    antonyms: List[str] = Field(default=[], description="A list of antonyms.")
    examples: List[str] = Field(..., min_length=2, description="At least two example sentences.")

def main():
    print("JSON definition generator\n")

    while True:
        prompt = input("Please input word, type exit to quit: ").strip()
        if prompt.lower() == "exit":
            break
        if not prompt:
            continue

        print("Generating response... \n")            
        resp = ask_model(prompt, 400)

        if resp:
            print("\n" + "="*20)
            data = resp.model_dump()
            print(f"Word: {data['word']}")
            print(f"Definition: {data['definition']}")
            print(f"Synonyms: {', '.join(data['synonyms']) if data['synonyms'] else 'N/A'}")
            print(f"Antonyms: {', '.join(data['antonyms']) if data['antonyms'] else 'N/A'}")
            print("Examples:")
            for ex in data['examples']:
                print(f"  - {ex}")
            print("="*20 + "\n")
    print("Exiting...")

if __name__=="__main__":
    main()