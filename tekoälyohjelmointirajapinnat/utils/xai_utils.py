import os
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system
from xai_sdk.tools import web_search, x_search

load_dotenv()

def get_api_key():
    try:
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            raise RuntimeError("XAI_API_KEY not set. Check your .env file or environment variables!")
        client = Client(api_key)
        return client

    except Exception as e:
        print(f"Error: xAI API key not found: {e}")

def news_summarizer(client, prompt, time_period):

    sys_prompt_summarizer = """
        You are a high-speed news summarizer/extractor. 
        Your job is to find news articles, as well as latest developments of the given topic, and format them clearly. 

        - Present the results as a numbered list.
        - For each item, provide the article's/posts title in bold.
        - Below the title, provide the source name, as well as how old the article/post is
        - A short summary (2-3 sentences) of the article/post
        - Lastly, provide the link to the article/post
        - Do not include any introductory or concluding sentences. Begin directly with the first item.

        Use tool calls sparingly (1-2 web searches, 1-2 X searches).
        """
    sys_prompt_aggregator = """
        You are a news link aggregator. 
        Your job is to find news articles/posts, as well as latest developments of the given topic.

        - Present the results as a numbered list.
        - For each item, provide the article's/posts title in bold and its direct URL.
        - Below the title, provide the source name
        - **Do not browse the pages or write summaries.**
        - Begin directly with the first item.
        """
    try:
        chat = client.chat.create(
            model="grok-4-fast",
            tools=[
                web_search(),
                x_search(),
            ]
        )
        chat.append(system(sys_prompt_summarizer),)
        chat.append(user(f"Topic: {prompt},Timeframe: {time_period}"))
        is_thinking = True
        final_response = None
        yield f"## Recent developments on {prompt} \n\n---\n\n"
        for response, chunk in chat.stream():
            for tool_call in chunk.tool_calls:
                print(f"\nCalling tool: {tool_call.function.name} with arguments: {tool_call.function.arguments}")
            if response.usage.reasoning_tokens and is_thinking:
                print(f"\rThinking... ({response.usage.reasoning_tokens} tokens)", end="", flush=True)
            if chunk.content and is_thinking:
                print("\n\nFinal Response:")
                is_thinking = False
            if chunk.content and not is_thinking:
                yield chunk.content
            final_response = response
            #print(response.content, end="", flush=True) # The response object auto-accumulates 
        print("\n\nUsage:")
        print(response.usage)
        print(response.server_side_tool_usage)
        print("\n\nServer Side Tool Calls:")
        print(response.tool_calls)

        
        if final_response and final_response.citations:
            yield "\n\n---\n\n## Citations \n"
            for i, citation in enumerate(final_response.citations, 1):
                citation_text = f"{i}: {citation}\n\n"
                yield citation_text
        

    except Exception as e:
        print(f"Error generating response: {e}") 
        yield f"An error occurred: {e}"