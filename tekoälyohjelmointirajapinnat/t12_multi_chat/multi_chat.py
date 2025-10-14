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
            label="Create me a workout routine",
            message="Can you create me a workout routine? Start by asking me my starting points. Start by asking things such as age, weight, how much I move, how fit I am etc.",
        ),

        cl.Starter(
            label="Explain object-oriented programming",
            message="Explain object-oriented programming to a non-technical person. You can assume they have no prior knowledge of the subject.",
        ),
        cl.Starter(
            label="Create a Tetris clone",
            message="Write me a simple Tetris clone in HTML/JS/CSS. The game must have increasing difficulty, and the next incoming piece must be shown to the user.",
            command="code",
        ),
        cl.Starter(
            label="Write an email to a customer to explain why they are wrong",
            message="Write a formal and professional email to a customer that explains why they are wrong on a subject.",
        )
    ]