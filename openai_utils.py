from pydantic import BaseModel
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import tiktoken

load_dotenv()

azure_openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

def get_parsed_completion(messages: list[dict], response_format: BaseModel):
    """
    Get parsed completion from Azure OpenAI.

    Args:
        messages (list[dict]): List of message dictionaries.
        response_format (BaseModel): The response format model.

    Returns:
        tuple: Parsed event, input token count, output token count.
    """
    completion = azure_openai_client.beta.chat.completions.parse(
        model=model_deployment_name,
        messages=messages,
        response_format=response_format,
    )
    output_token = completion.usage.completion_tokens
    input_token = completion.usage.prompt_tokens
    event = completion.choices[0].message.parsed
    return event, input_token, output_token

def get_token_count(text: str) -> int:
    """
    Get the number of tokens in a given text.

    Args:
        text (str): The input text.

    Returns:
        int: The number of tokens.
    """
    enc = tiktoken.get_encoding("o200k_base")
    tokens = enc.encode(text)
    return len(tokens)

def estimate_cost_for_gpt4o_0806(input_tokens: int, output_tokens: int) -> float:
    """
    Estimate the cost for GPT-4o-0806 model usage.

    Args:
        input_tokens (int): Number of input tokens.
        output_tokens (int): Number of output tokens.

    Returns:
        float: Estimated cost in USD.
    """
    return (input_tokens / 1000) * 0.0025 + (output_tokens / 1000) * 0.01