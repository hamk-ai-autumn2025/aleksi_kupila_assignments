import chainlit as cl
from openrouter_utils import call_openrouter_api

@cl.on_chat_start
def on_chat_start():
    print("A new chat session has started!")


@cl.on_message
async def main(message: cl.Message):
    print(f"User sent: {message.content}")
    resp = call_openrouter_api(message.content, model="x-ai/grok-4-fast")

    if resp:
        await cl.Message(
            content=resp,
        ).send()
    else:
        await cl.Message(
            content=f"Error fetching response",
        ).send()