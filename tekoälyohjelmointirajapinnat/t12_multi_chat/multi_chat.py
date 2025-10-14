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
                values=["x-ai/grok-4-fast", "google/gemini-2.0-flash-001", "deepseek/deepseek-chat-v3-0324", "openai/gpt-5-nano"],
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