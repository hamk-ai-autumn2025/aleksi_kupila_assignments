import chainlit as cl
from openrouter_utils import call_openrouter_api
from chainlit.input_widget import Select

@cl.on_chat_start
async def on_chat_start():
    print("A new chat session has started!")
    
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="OpenAI - Model",
                values=["x-ai/grok-4-fast", "google/gemini-2.0-flash-001", "deepseek/deepseek-chat-v3-0324", "openai/gpt-5-nano", "openai/gpt-4o", "openai/gpt-4o-mini", "openai/gpt-4-turbo", "anthropic/claude-3-5-sonnet-20241022", "anthropic/claude-3-haiku-20240307", "meta-llama/llama-3.1-405b-instruct", "meta-llama/llama-3.1-70b-instruct", "meta-llama/llama-3.1-8b-instruct", "google/gemini-pro-1.5", "google/gemini-flash-1.5", "mistralai/mistral-7b-instruct", "mistralai/mixtral-8x7b-instruct", "cohere/command-r-plus", "cohere/command-r", "fireworks/firefunction-v2", "togethercomputer/llama-2-70b-chat"],
                initial_index=0,
            ),
        ]
    ).send()
    cl.user_session.set("model", settings["Model"])

@cl.on_settings_update
async def setup_agent(settings):
    print("on_settings_update", settings)
    cl.user_session.set("model", settings["Model"])

@cl.on_message
async def main(message: cl.Message):
    print(f"User sent: {message.content}")
    # Get the selected model from chat settings
    model = cl.user_session.get("model")

    resp = call_openrouter_api(message.content, model=model)

    if resp:
        await cl.Message(
            author=model,
            content=resp,
        ).send()
    else:
        await cl.Message(
            content=f"Error fetching response",
        ).send()

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Morning routine ideation",
            message="Can you help me create a personalized morning routine that would help increase my productivity throughout the day? Start by asking me about my current habits and what activities energize me in the morning.",
        ),

        cl.Starter(
            label="Explain superconductors",
            message="Explain superconductors like I'm five years old.",
        ),
        cl.Starter(
            label="Python script for daily email reports",
            message="Write a script to automate sending daily email reports in Python, and walk me through how I would set it up.",
            command="code",
        ),
        cl.Starter(
            label="Text inviting friend to wedding",
            message="Write a text asking a friend to be my plus-one at a wedding next month. I want to keep it super short and casual, and offer an out.",
        )
    ]