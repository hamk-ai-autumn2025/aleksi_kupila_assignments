from openai import OpenAI
import replicate
import requests
import argparse
import base64
from file_util import find_new_file_name

client=OpenAI()

# Encode image. Return false in case of invalid path or other error
def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8").replace("\n", "")
    except Exception as e:
        print(f'Invalid image path: {e}')
        return False
    
def generateDescription(image_path, model):

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
            print(f"{response.output_text}\n")
            return response.output_text

        except Exception as e:
            print(f"Error generating description: {e}\n")
    return False

# Generates image and saves it on a file
def generateImage(description):
    model = "bytedance/seedream-4" #"stability-ai/stable-diffusion-3.5-large-turbo" #"bytedance/seedream-4" #"black-forest-labs/flux-dev" 
    print("---Generating image based on the description---")
    print(f"---Using image generation model: {model}---\n")
    input={
        "prompt": f"photorealistic,ultra realistic,best quality,{description}",
        #"aspect_ratio": "3:2",
        #"negative_prompt": "lowres,blur,low quality,mistake,error",
        #"disable_safety_checker":True
    }
    try:
        output = replicate.run(model, input=input)

        # For SD3.5 Turbo
        '''
        print(output.url)
        file_name = find_new_file_name("img2txt.png")
        with open(file_name, "wb") as file:
            file.write(output.read())
        '''

        # For flux-dev, flux-schnell etc.

        for url in output:
            print(f"Image URL: {url}")
            data = requests.get(url).content
            file_name = find_new_file_name("img2txt.png")
            with open(file_name, "wb") as f:
                f.write(data)
                print(f"Image saved to {file_name}")

    except Exception as e:
        print(f"Error generating image: {e}\n")
    
# Return true if user inputs are valid
def check(path,model):
    allowed_modelsDesc=["gpt-5","gpt-5-mini","gpt-5-nano","gpt-4.1","gpt-4.1-nano","gpt-4o","gpt-4o-mini"]
    # allowed_modelsImg=["black-forest-labs/flux-dev","bytedance/seedream-4"]
    if path and model:
        if len(path)>5:
            if model in allowed_modelsDesc:
                print("Proceeding to generate...")
                return True
            else:
                print("Model not allowed! Aborting...")
        else:
            print("The path is too short! Aborting...")
    else:
        print("One or more empty parameters! Aborting...")
    return False


def main():

    parser = argparse.ArgumentParser(
        prog="Img2Text Bot",
        description="Prompts AI to create a description of an image. Then generates a new image based on the description."
    )
    parser.add_argument('file_path', help="Path to the (local) file to be processed")
    parser.add_argument('-m', '--model', type=str, default="gpt-4.1-nano", help="The LLM used to generate the text description: Options are: gpt-5, gpt-5-mini, gpt-5-nano, gpt-4.1, gpt-4.1-nano, gpt-4o, gpt-4o-mini")
    args = parser.parse_args()

    print("Welcome to img2text program interface!\n")
    path=args.file_path
    model = args.model

    if check(path, model):
        description = generateDescription(path,model)
        if description:
            generateImage(description)
        else:
            print("Quitting...")
    
if __name__=="__main__":
    main()