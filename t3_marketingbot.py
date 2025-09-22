from openai import OpenAI

client=OpenAI()

def generate(request, model, n):

    supports_sampling = model not in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
    SYSTEM_PROMPT = """
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
    param_sets = [(0.5, 0.9), (0.7, 0.95), (0.9, 1.0)]
    for i, (temp, top_p) in enumerate(param_sets, start=1):
        print(f"---Version {i} (Temperature = {temp if supports_sampling else 'N/A'})---\n")

        try:
            response = client.responses.create(
                input=request,
                instructions=SYSTEM_PROMPT,
                model=model,
                **({"temperature": temp, "top_p": top_p} if supports_sampling else {}),  # Only enter these if model is not GPT-5 (supports sampling)
                max_output_tokens=2000,
            )
            # Prints output for both GPT-5 and others
            print(f"{response.output_text}\n")


        except Exception as e:
            print(f"Error generating version {i+1}: {e}\n")


# Return true if user inputs are valid
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
    prompt = input("Enter prompt for marketing material: ")
    model = input("Model choice: ")

    if check(prompt,model):
        generate(prompt,model,3)

if __name__=="__main__":
    main()