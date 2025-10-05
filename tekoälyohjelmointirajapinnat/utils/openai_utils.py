import os
from openai import OpenAI
from utils.file_util import find_new_file_name
import base64

client = OpenAI()

def create_translation(recording, model="gpt-4o-mini-transcribe", saveOutput=False, removeFile = True) -> str:
    '''
    Returns string transcription of an audio file, translated into English. Uses OpenAI API.

    Args:
        Audio file path (str), LLM to use (str), Save output to a text file (bool), Remove audio file afterwards (bool)

    Returns:
        String transcription (English) of the speech in the audio file
    '''
    print ("--- Transcribing... ---")

    with open (recording, "rb") as audio_file:
        try:
            transcription = client.audio.translations.create(
            model=model, 
            file=audio_file,
            )
            print(f'Transcription: {transcription.text}\n')
            if saveOutput:
                filename = find_new_file_name("transcription.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(transcription.text)
                    print(f"Final output saved to {filename}")
            
        except Exception as e:
            print(f'Error creating transcription: {e}')
            return None

 # Remove file after successful processing
    if removeFile:
        try:
            os.remove(recording)
            print(f"Removed audio file: {recording}")
        except OSError as e:
            print(f"Error removing file {recording}: {e}")
            
    return transcription.text
            
    
def create_transcription(recording, model="gpt-4o-transcribe", saveOutput=False, removeFile=True) -> str:
    '''
    Returns string transcription of an audio file in spoken language. Uses OpenAI API.

    Args:
        Audio file path (str), LLM to use (str), Save output to a text file (bool), Remove audio file afterwards (bool)

    Returns:
        String transcription of the speech in the audio file
    '''
    print ("--- Transcribing... ---")

    with open (recording, "rb") as audio_file:
        try:
            transcription = client.audio.transcriptions.create(
            model=model, 
            file=audio_file,
            )
            print(f'Transcription: {transcription.text}\n')
            if saveOutput:
                filename = find_new_file_name("transcription.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(transcription.text)
                    print(f"Final output saved to {filename}")
        except Exception as e:
            print(f'Error creating transcription: {e}')
            return None
        
    if removeFile:
        try:
            os.remove(recording)
            print(f"Removed audio file: {recording}")
        except OSError as e:
            print(f"Error removing file {recording}: {e}")
    return transcription.text

# --- Image related ---
def encode_image(image_path):
    '''
    Used by generateDescription
    '''
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8").replace("\n", "")
    except Exception as e:
        print(f'Invalid image path: {e}')
        return False
    

def generate_image_description(image_path, model):
    '''
    Function for generating a description of an image
    '''
    supports_sampling = model not in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
    print("---Generating description of image...---")
    print(f"---Using description generation model: {model}---\n")

    base64_image = encode_image(image_path)
    if base64_image:
        try:
            response = client.responses.create(
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Describe this image in detail."
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        ]
                    }
                ],
                model=model,
                **({"temperature": 0.6, "top_p": 0.95} if supports_sampling else {}),  # Only enter these if model is not GPT-5 (supports sampling)
                max_output_tokens=2000,
            )
            # Prints output for both GPT-5 and others
            print(f"Response:\n{response.output_text}\n")
            return response.output_text

        except Exception as e:
            print(f"Error generating description: {e}\n")
    return False

def generate_marketing_material(image_paths, prompt, model):
    '''
    Function for generating a marketing speech and 3 slogans for a product
    '''
    supports_sampling = model not in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
    print("---Generating description of image...---")
    print(f"---Using description generation model: {model}---\n")

    sysprompt = """You are a marketing assistant. 
    Given an image of a product and optional user input about its features or target audience, generate:

    1. A 3-4 sentence "sales speech" that highlights the product's main benefits and appeals to customers. 
    2. Three short, catchy marketing slogans (1-6 words each).

    Always return the result in JSON format like this:

    {
        "description": "...",
        "slogans": ["...", "...", "..."]
    }

    Do not include any text outside of the JSON object."""

    for img in image_paths:
        base64_image = encode_image(img)

    if base64_image:
        try:
            response = client.responses.create(
                instructions = sysprompt,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": f"{prompt}"
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        ]
                    }
                ],
                model=model,
                **({"temperature": 0.6, "top_p": 0.95} if supports_sampling else {}),  # Only enter these if model is not GPT-5 (supports sampling)
                max_output_tokens=2000,
            )
            # Prints output for both GPT-5 and others
            print(f"Response:\n{response.output_text}\n")
            return response.output_text

        except Exception as e:
            print(f"Error generating description: {e}\n")
    return False