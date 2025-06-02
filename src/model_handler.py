import requests
import json
import os
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the API endpoint from an environment variable or use a default
MODEL_API_URL = os.environ.get("MODEL_API_URL", "https://juanvic-Bob.hf.space/")

# Chat generation function
def generate_reply(user_input: str,
                    max_new_tokens: int = 80,
                    temperature: float = 0.7,
                    top_p: float = 0.9) -> str:
    """Sends a request to the external FastAPI model server for text generation.

    Args:
        user_input (str): The user's message.
        max_new_tokens (int): Max tokens to generate.
        temperature (float): Sampling temperature.
        top_p (float): Nucleus sampling probability.
    Returns:
        str: The assistant's reply.
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "user_input": user_input,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }

    try:
        logger.info(f"Sending request to {MODEL_API_URL} with input: {user_input[:50]}...")
        response = requests.post(MODEL_API_URL, headers=headers, data=json.dumps(payload), timeout=210) #limit timeout issues
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        
        result = response.json()
        logger.info(f"Received response: {str(result)[:100]}...")

        if "reply" in result:
            return result["reply"].strip()
        else:
            logger.warning(f"Unexpected response format from API: {result}")
            return "⚠️ Error: Could not parse the model's response from API."

    except requests.exceptions.Timeout:
        logger.error(f"Request to {MODEL_API_URL} timed out.")
        return "⚠️ Error: The request to the model API timed out."
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling model API at {MODEL_API_URL}: {e}")
        return f"⚠️ Error: Could not reach the model service ({e})."
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON response from {MODEL_API_URL}")
        return "⚠️ Error: Invalid response format from the model API."
