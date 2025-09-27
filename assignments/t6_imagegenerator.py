import replicate
import requests
import argparse
from random import randint
from aleksiK_assignments.assignments.utils.file_util import find_new_file_name

def generateImage(args):

    print("---Generating image based on the description---")
    print(f"---Using image generation model: {args.model}---")
    print(f'Prompt: {args.prompt}')
    print(f'Aspect ratio: {args.aspect_ratio}, seed: {args.seed}, output format: {args.output_format}, quantity: {args.quantity}, allow NSFW: {args.safety_checker}\n')
    input={
        "prompt": args.prompt,
        "aspect_ratio": args.aspect_ratio,
        #"negative_prompt": args.negative_prompt,  # Do not use with Flux-dev or flux-schnell
        "disable_safety_checker":args.safety_checker,
        "num_outputs": args.quantity,
        "output_format": args.output_format,
        "seed": args.seed,

    }
    try:
        output = replicate.run(args.model, input=input)

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
            file_name = find_new_file_name(f"{args.prompt[:10]}.{args.output_format}")
            with open(file_name, "wb") as f:
                f.write(data)
                print(f"Image saved to {file_name}")

    except Exception as e:
        print(f"Error generating image: {e}\n")

def validate_args(args):
        approved_models = ["black-forest-labs/flux-dev", "black-forest-labs/flux-schnell", "bytedance/seedream-4"]
        approved_aspect_ratios = ["1:1", "3:2", "2:3", "16:9", "9:16"]
        approved_formats = ["png", "jpg", "jpeg", "webp"]

        if args.model not in approved_models:
            print(f"Error: Model '{args.model}' is not approved. Choose from: {', '.join(approved_models)}")
            return False
        if args.aspect_ratio not in approved_aspect_ratios:
            print(f"Error: Aspect ratio '{args.aspect_ratio}' is not approved. Choose from: {', '.join(approved_aspect_ratios)}")
            return False
        if args.output_format not in approved_formats:
            print(f"Error: Format '{args.output_format}' is not approved. Choose from: {', '.join(approved_formats)}")
            return False
        if args.quantity < 1 or args.quantity > 4:
            print("Error: Quantity must be between 1 and 4.")
            return False
        if args.seed is not None and (args.seed < 0 or args.seed > 999999):
            print("Error: Seed must be between 0 and 999999.")
            return False
        if not args.prompt or not isinstance(args.prompt, str) or len(args.prompt)>800:
            print("Error: Prompt must be a non-empty string and under 400 characters long.")
            return False
  
        return True

def main():

    parser = argparse.ArgumentParser(
        prog="Image Generator",
        description="Generates images using AI models based on text prompts."
    )
    parser.add_argument('-p', '--prompt', type=str, default="Ultra realistic, photorealistic, African man flying in a large, realistic, full-sized wooden helicopter", help="Input prompt for the image generator.")
    parser.add_argument('-n', '--negative_prompt', type=str, default="lowres,blur,low quality,mistake,deformed", help="Negative prompt for the generated image. Only used in certain models.")
    parser.add_argument('-m', '--model', type=str, default="black-forest-labs/flux-schnell", help="The model used to generate images: Options are: black-forest-labs/flux-dev, black-forest-labs/flux-schnell")
    parser.add_argument('-a', '--aspect_ratio',type=str, default="1:1", help="Aspect ratio of the generated image.")
    parser.add_argument('-f', '--output_format', type=str, default="webp", help='Output format of the generated image.')
    parser.add_argument('-s', '--seed', type=int, default=randint(0,999999),help='Custom seed for the generated image.' )
    parser.add_argument('-q', '--quantity', type=int, default=1, help='Quantity of images generated.')
    parser.add_argument('-c', '--safety_checker', action='store_true', default=False, help="Filters out NSFW content.")
    args = parser.parse_args()

    print("Welcome to image generator program interface!\n")
    if not validate_args(args):
        print("Exiting due to invalid arguments.")
        return
    generateImage(args)
    print('Exiting...')
    
if __name__=="__main__":
    main()