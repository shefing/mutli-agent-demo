# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import inspect
import json
import logging
import os
import sys
import traceback
import requests
from dotenv import load_dotenv

from typing import Any, Callable, Dict, List
from rich import print

from openai import OpenAI

from llamafirewall import LlamaFirewall, ScanDecision, ScannerType
from llamafirewall.llamafirewall_data_types import (
    AssistantMessage,
    Role,
    ToolMessage,
    UserMessage,
)

# Load environment variables from .env file
load_dotenv()

# logging configs
logger = logging.getLogger(__name__)
#logger.setLevel(logging.WARN)  # Set the logging level
logger.setLevel(logging.DEBUG)  # Change from WARN to DEBUG

logger.propagate = False
formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d - %H:%M:%S"
)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


# Note: To use the websearch and extract_url functions, install the tavily package:
# pip install tavily-python
try:
    from tavily import TavilyClient

    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logger.warning(
        "[bold yellow]Warning: Tavily package not found. Web search functionality will be limited.[/bold yellow]"
    )


# Initialize the OpenAI client based on available API keys
# If LLAMA_API_KEY is available, use it with the Llama API
# Otherwise, fall back to OPENAI_API_KEY for OpenAI's API
if os.getenv("LLAMA_API_KEY"):
    client = OpenAI(
        api_key=os.getenv("LLAMA_API_KEY"), 
        base_url=os.getenv("LLAMA_API_BASE_URL")
    )
    using_llama_api = True
    print("[bold green]Using Llama API[/bold green]")
elif os.getenv("OPENAI_API_KEY"):
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    using_llama_api = False
    print("[bold yellow]Using OpenAI API (Llama API not available)[/bold yellow]")
else:
    raise ValueError("No API key found. Please set either LLAMA_API_KEY or OPENAI_API_KEY in your .env file.")

# Initialize LlamaFirewall with CODE_SHIELD scanner for all roles and AGENT_ALIGNMENT for ASSISTANT
llama_firewall = LlamaFirewall(
    scanners={
        Role.USER: [ScannerType.CODE_SHIELD],
        Role.SYSTEM: [ScannerType.CODE_SHIELD],
        Role.ASSISTANT: [ScannerType.CODE_SHIELD, ScannerType.AGENT_ALIGNMENT],
        Role.TOOL: [ScannerType.CODE_SHIELD],
    }
)


def function_to_tool_schema(func: Callable) -> Dict[str, Any]:
    """
    Convert a Python function to the tool schema format required by LlamaAPIClient.

    Args:
        func: The Python function to convert

    Returns:
        A dictionary representing the tool schema
    """
    # Get function signature
    sig = inspect.signature(func)

    # Get function docstring for description
    description = inspect.getdoc(func) or f"Function to {func.__name__}"

    # Build parameters schema
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        # Skip self parameter for methods
        if param_name == "self":
            continue

        param_type = "string"  # Default type
        param_desc = ""

        # Try to get type annotation
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == str:
                param_type = "string"
            elif param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"

        # Add parameter to properties
        properties[param_name] = {
            "type": param_type,
            "description": param_desc
            or f"Parameter {param_name} for function {func.__name__}",
        }

        # Add to required list if no default value
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    # Build the complete tool schema
    tool_schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
            "strict": True,
        },
    }

    return tool_schema


def websearch(query: str) -> str:
    """
    Perform a web search for the given query using Tavily API.

    Args:
        query: The search query

    Returns:
        Search results from Tavily
    """
    if not TAVILY_AVAILABLE:
        return "Error: Tavily package not installed. Please install with 'pip install tavily-python'."

    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        return "Error: Tavily API key not found in environment variables. Please add TAVILY_API_KEY to your .env file."

    try:
        # Initialize Tavily client
        tavily_client = TavilyClient(api_key=tavily_api_key)

        # Perform search
        result = tavily_client.search(query, search_depth="basic", max_results=5)

        # Format the results
        formatted_results = f"Search results for '{query}':\n\n"

        for i, item in enumerate(result.get("results", []), 1):
            title = item.get("title", "No title")
            content = item.get("content", "No content")
            url = item.get("url", "No URL")

            formatted_results += f"{i}. **{title}**\n"
            formatted_results += f"   {content[:200]}...\n"
            formatted_results += f"   Source: {url}\n\n"

        if not result.get("results"):
            formatted_results += "No results found."

        return formatted_results

    except Exception as e:
        return f"Error performing web search: {str(e)}"


def fetch_url_content_pre_rendering(url):
    """
    Fetches the HTML content from the provided URL with additional logging for debugging.

    Args:
        url (str): The URL of the page to fetch.

    Returns:
        str: The HTML content of the page if successful.

    Raises:
        requests.RequestException: If the HTTP request fails.
    """

    try:
        logger.debug("Attempting to fetch URL: %s", url)

        response = requests.get(url)

        logger.debug("Received response with status code: %d", response.status_code)
        logger.debug("Sample content %s", response.text[:1000])

        # This will raise an HTTPError for 400, 500, etc.
        response.raise_for_status()

        html = response.text
        logger.debug(
            "Successfully fetched content; content length: %d characters", len(html)
        )
        return html

    except requests.RequestException as e:
        logger.error("Request failed with error: %s", e)

        # If we have a response object, log part of its text for debugging.
        if "response" in locals() and response is not None:
            content_preview = response.text[:500]  # print first 500 characters
            logger.error("Response content preview: %s", content_preview)
        raise


async def call_openai_responses_api(prompt: str) -> str:
    """
    Call the OpenAI /v1/responses API endpoint directly.

    This is an alternative to the chat completions API that works with project-specific API keys.

    Args:
        prompt: The user's prompt

    Returns:
        The model's response text
    """
    import requests

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": model,
        "input": prompt,
        "store": True
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json().get("output", "No response received")
    except Exception as e:
        logger.error(f"Error calling OpenAI responses API: {str(e)}")
        if response and hasattr(response, 'text'):
            logger.error(f"Response content: {response.text}")
        raise

async def interact_with_ai(
    user_message: str,
    messages: List[Dict[str, Any]],
    model=None,
) -> List[Dict[str, Any]]:
    """
    Interact with AI agent using OpenAI API with tools.

    Args:
        user_message: User's message
        messages: Chat history as a list of Message objects
        model: Model to use for the interaction. If None, uses the default based on the API.

    Returns:
        Updated chat history as a list of Message objects
    """
    # If model is not specified, use the appropriate default based on the API being used
    if model is None:
        if using_llama_api:
            model = os.getenv("LLAMA_API_MODEL", "Llama-4-Scout-17B-16E-Instruct-FP8")
        else:
            model = "gpt-3.5-turbo"  # Default OpenAI model
    # Define available tools
    available_tools: Dict[str, Callable] = {
        "websearch": websearch,
        "fetch_url_content_pre_rendering": fetch_url_content_pre_rendering,
    }

    # Convert functions to tool schemas
    tools = [function_to_tool_schema(func) for func in available_tools.values()]

    # Add the current user message to our history
    user_msg = UserMessage(content=user_message)

    messages.append(
        {
            "role": Role.USER.value,
            "content": user_message,
        }
    )

    # Scan the user message
    result = await llama_firewall.scan_async(user_msg)

    if result.decision == ScanDecision.BLOCK:
        response = f"Blocked by LlamaFirewall, {result.reason}"
        messages.append(
            {
                "role": Role.ASSISTANT.value,
                "content": response,
            }
        )

        return messages

    try:
        # Check if we're using a project-specific OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        using_project_key = not using_llama_api and openai_api_key.startswith("sk-proj-")

        # If using a project-specific key, use the /v1/responses endpoint
        if using_project_key:
            logger.debug("Using OpenAI /v1/responses API with project-specific key")
            # Combine all messages into a single prompt
            combined_prompt = ""
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if content:
                    combined_prompt += f"{role}: {content}\n\n"

            # Add the current user message
            combined_prompt += f"user: {user_message}\n\nassistant:"

            try:
                # Call the /v1/responses API
                response_text = await call_openai_responses_api(combined_prompt)

                # Scan the assistant's response with LlamaFirewall
                # Ensure response_text is a string
                if isinstance(response_text, list):
                    # Check if the list contains dictionaries
                    if response_text and isinstance(response_text[0], dict):
                        # Extract text from dictionaries if possible
                        extracted_texts = []
                        for item in response_text:
                            if isinstance(item, dict) and 'text' in item:
                                text_content = item['text']
                                if isinstance(text_content, list):
                                    # If text_content is a list, flatten it
                                    extracted_texts.extend([str(subitem) for subitem in text_content])
                                else:
                                    extracted_texts.append(str(text_content))
                            elif isinstance(item, dict) and 'content' in item:
                                content_value = item['content']
                                if isinstance(content_value, list):
                                    # If content_value is a list, flatten it
                                    extracted_texts.extend([str(subitem) for subitem in content_value])
                                else:
                                    extracted_texts.append(str(content_value))
                            else:
                                # If we can't extract text, convert the whole dict to string
                                extracted_texts.append(str(item))
                        response_text = ' '.join(extracted_texts)
                    else:
                        # If it's a list of strings or other simple types
                        response_text = ' '.join(str(item) for item in response_text)
                assistant_msg = AssistantMessage(content=response_text)
                # Convert messages to a trace for the AGENT_ALIGNMENT scanner
                trace = []
                for msg in messages:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role == Role.USER.value:
                        trace.append(UserMessage(content=content))
                    elif role == Role.ASSISTANT.value:
                        trace.append(AssistantMessage(content=content))
                    elif role == Role.TOOL.value:
                        trace.append(ToolMessage(content=content))

                # Add the current user message to the trace if it's not already there
                if not any(isinstance(msg, UserMessage) and msg.content == user_message for msg in trace):
                    trace.append(UserMessage(content=user_message))

                # Log the trace for debugging
                logger.debug(f"Scanning assistant message with trace of {len(trace)} messages")
                logger.debug(f"Assistant message content: {assistant_msg.content[:100]}...")

                assistant_scan_result = await llama_firewall.scan_async(assistant_msg, trace)

                # Log the scan result for debugging
                logger.debug(f"AGENT_ALIGNMENT scan result: decision={assistant_scan_result.decision}, score={assistant_scan_result.score}")
                if assistant_scan_result.reason:
                    logger.debug(f"AGENT_ALIGNMENT scan reason: {assistant_scan_result.reason[:200]}...")

                if assistant_scan_result.decision != ScanDecision.ALLOW:
                    logger.info(f"Assistant message blocked: {assistant_scan_result.reason}")
                    response_text = f"Blocked by LlamaFirewall: {assistant_scan_result.reason}"

                # Add the response to messages
                messages.append({
                    "role": Role.ASSISTANT.value,
                    "content": response_text,
                })

                # Return the updated messages
                return messages

            except Exception as e:
                raise Exception(f"Error calling OpenAI /v1/responses API: {str(e)}")

        # Otherwise, use the standard chat completions API
        # Start the Agent loop
        tool_call = True
        while tool_call:
            # debug last message
            logger.debug(f"messages: {messages[-1]}")

            # Call Llama API with tools enabled
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2048,
                temperature=0.7,
                tools=tools,
            )

            logger.debug(f"response: {response}")
            # Get the response message
            response_message = response.choices[0].message

            messages.append(
                {
                    "role": response_message.role,
                    "content": response_message.content,
                    "tool_calls": response_message.tool_calls,
                }
            )

            # Check if there are tool calls
            if hasattr(response_message, "tool_calls") and response_message.tool_calls:
                # Process each tool call
                for tool_call in response_message.tool_calls:
                    # Execute the tool
                    tool_name = tool_call.function.name
                    if tool_name in available_tools:
                        try:
                            # Parse arguments
                            arguments = json.loads(tool_call.function.arguments)

                            # Call the function
                            tool_result = available_tools[tool_name](**arguments)

                            tool_msg = ToolMessage(content=str(tool_result))

                            # Scan the tool result
                            lf_result = await llama_firewall.scan_async(tool_msg)

                            if lf_result.decision == ScanDecision.BLOCK:
                                # for demonstration purposes, we show the tool output, but this should be avoided in production
                                blocked_response = f"Blocked by LlamaFirewall: {lf_result.reason} - Tool result: {tool_result}"
                                tool_result = blocked_response

                            # Add tool result to messages
                            messages.append(
                                {
                                    "role": Role.TOOL.value,
                                    "tool_call_id": tool_call.id,
                                    "content": tool_result,
                                }
                            )

                        except Exception as e:
                            # Add error message if tool execution fails
                            error_msg = f"Error: {str(e)}"
                            tool_msg = AssistantMessage(content=error_msg)
                            messages.append(
                                {
                                    "role": Role.TOOL.value,
                                    "tool_call_id": tool_call.id,
                                    "content": error_msg,
                                }
                            )
                            logger.error(f"\nTool Error: {error_msg}")

                        logger.debug(f"Tool Call response: {messages[-1]}")

                # Continue the loop to get the next response
                continue
            else:
                # No tool calls, add the response to history and break the loop
                tool_call = False
                full_response = response_message.content

                # Scan the assistant's response with LlamaFirewall
                # Ensure full_response is a string
                if isinstance(full_response, list):
                    # Check if the list contains dictionaries
                    if full_response and isinstance(full_response[0], dict):
                        # Extract text from dictionaries if possible
                        extracted_texts = []
                        for item in full_response:
                            if isinstance(item, dict) and 'text' in item:
                                text_content = item['text']
                                if isinstance(text_content, list):
                                    # If text_content is a list, flatten it
                                    extracted_texts.extend([str(subitem) for subitem in text_content])
                                else:
                                    extracted_texts.append(str(text_content))
                            elif isinstance(item, dict) and 'content' in item:
                                content_value = item['content']
                                if isinstance(content_value, list):
                                    # If content_value is a list, flatten it
                                    extracted_texts.extend([str(subitem) for subitem in content_value])
                                else:
                                    extracted_texts.append(str(content_value))
                            else:
                                # If we can't extract text, convert the whole dict to string
                                extracted_texts.append(str(item))
                        full_response = ' '.join(extracted_texts)
                    else:
                        # If it's a list of strings or other simple types
                        full_response = ' '.join(str(item) for item in full_response)
                assistant_msg = AssistantMessage(content=full_response)
                # Convert messages to a trace for the AGENT_ALIGNMENT scanner
                trace = []
                for msg in messages:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role == Role.USER.value:
                        trace.append(UserMessage(content=content))
                    elif role == Role.ASSISTANT.value:
                        trace.append(AssistantMessage(content=content))
                    elif role == Role.TOOL.value:
                        trace.append(ToolMessage(content=content))

                # Add the current user message to the trace if it's not already there
                if not any(isinstance(msg, UserMessage) and msg.content == user_message for msg in trace):
                    trace.append(UserMessage(content=user_message))

                # Log the trace for debugging
                logger.debug(f"Scanning assistant message with trace of {len(trace)} messages")
                logger.debug(f"Assistant message content: {assistant_msg.content[:100]}...")

                assistant_scan_result = await llama_firewall.scan_async(assistant_msg, trace)

                # Log the scan result for debugging
                logger.debug(f"AGENT_ALIGNMENT scan result: decision={assistant_scan_result.decision}, score={assistant_scan_result.score}")
                if assistant_scan_result.reason:
                    logger.debug(f"AGENT_ALIGNMENT scan reason: {assistant_scan_result.reason[:200]}...")

                if assistant_scan_result.decision != ScanDecision.ALLOW:
                    logger.info(f"Assistant message blocked: {assistant_scan_result.reason}")
                    full_response = f"Blocked by LlamaFirewall: {assistant_scan_result.reason}"

                messages.append(
                    {
                        "role": Role.ASSISTANT.value,
                        "content": full_response,
                    }
                )

    except Exception as e:
        error_message = f"Error calling API: {str(e)}"
        traceback.print_exc()

        # Provide more helpful guidance for common API errors
        error_str = str(e)
        if "model_not_found" in error_str or "does not have access to model" in error_str:
            error_message += "\n\nThis error occurs because your API key doesn't have access to the requested model. Please check:\n"
            error_message += "1. If you're using a project-specific API key (starts with 'sk-proj-'), try using a standard API key instead\n"
            error_message += "2. Verify that your OpenAI account has access to the model being requested\n"
            error_message += "3. See the 'OpenAI Model Access Error' section in the README.md for more details"
        elif "invalid_api_key" in error_str or "authentication" in error_str.lower():
            error_message += "\n\nThis error indicates an issue with your API key. Please check:\n"
            error_message += "1. That you've provided a valid API key in your .env file\n"
            error_message += "2. That the API key format is correct (standard OpenAI keys start with 'sk-')\n"
            error_message += "3. That your API key hasn't expired or been revoked"

        messages.append(
            {
                "role": Role.ASSISTANT.value,
                "content": error_message,
            }
        )

    logger.debug(f"Assistant response: {messages[-1]}")

    return messages


async def run_demo():
    """
    Run the agent in console mode, taking input from the command line.
    """
    print(
        "[bold green]Starting AI Agent in console mode. Type 'exit' to quit.[/bold green]"
    )
    messages: List[Dict[str, Any]] = []

    # Model will be determined in interact_with_ai based on the API being used
    model = None

    while True:
        user_message = input("\nYou: ")
        if user_message.lower() == "exit":
            break

        messages = await interact_with_ai(user_message, messages, model)

        logger.info(f"Full history: {messages}")

        # Print the assistant's response
        if messages:
            assistant_message = messages[-1]["content"]
            print(f"\n[bold green]Assistant:[/bold green] {assistant_message}")


if __name__ == "__main__":
    import asyncio

    # Run the demo
    asyncio.run(run_demo())
