from openai import OpenAI

client=OpenAI()

def generate(request, model, n):

    for i in range(n):
        print(f"---Version {i+1}---\n")
        sysprompt = """
        Role & Background:
        You are a marketing expert, specialized in creating short, energetic ad speeches for different products and services.

        Style & Tone:
        - Energetic, persuasive, and memorable.
        - Designed for 10–30 second video ads (e.g., YouTube, TikTok).
        - Begin by appealing to emotions or personal experiences of the audience.
        - End with a clear call to action (CTA).
        - Avoid jargon; keep language simple, punchy, and relatable.
        - SEO-optimized: use multiple synonyms and keywords for the product or service.

        Format Guidelines:
        - Keep output short (3–6 sentences max).
        - Use rhetorical questions, bold statements, or relatable scenarios to hook the viewer.
        - Vary style slightly depending on product category (tech, food, lifestyle, etc.).

        Examples:
        - Are you letting inattention get ahead of you? Try our latest energy drink!
        - Tired of your phone dying when you need it most? Our power bank keeps you connected all day.
        - What if learning felt exciting again? With our app, it does.
        """

        response=client.responses.create(
            input=request,
            instructions=sysprompt,
            model=model,
            temperature=0.9,
            max_output_tokens=500,
            stream=False
        )
    print(response.output_text)

def check(request,model):
    allowed_models=["gpt-5","gpt-5-mini","gpt-5-nano","gpt-4.1","gpt-4.1-nano","gpt-4o","gpt-4o-mini"]
    if request and model:
        if len(request)>5:
            if model in allowed_models:
                print("Valid inputs! Proceeding to generate...")
                return True
            else:
                print("Model not allowed! Aborting...")
        else:
            print("The prompt is too short! Aborting...")
    else:
        print("One or more empty parameters! Aborting...")
    return False



def main():
    print("Welcome to marketing material bot interface!\n")
    request = input("Enter prompt for marketing material: ")
    model = input("Model choice: ")

    if check(request,model):
        generate(request,model,1)

if __name__=="__main__":
    main()