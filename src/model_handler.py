import requests
import json
import os
import logging
import random

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the API endpoint from an environment variable or use a default.  This allows for easy configuration of the API URL without changing the code.
MODEL_API_URL = os.environ.get("MODEL_API_URL", "https://juanvic-Bob2.hf.space/")
MODEL_API_URL = os.environ.get("MODEL_API_URL", "https://juanvic-Bob.hf.space/")

api_urls = [
    "https://juanvic-Bob2.hf.space/",
    "https://juanvic-Bob.hf.space/"
]
MODEL_API_URL = os.environ.get("MODEL_API_URL", random.choice(api_urls))

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

    try: # Uses a try-except block to handle potential network issues (timeouts, connection errors, etc.)
        logger.info(f"Sending request to {MODEL_API_URL} with input: {user_input[:50]}...")
        response = requests.post(MODEL_API_URL, headers=headers, data=json.dumps(payload), timeout=210) #Sends the request to the API endpoint with headers, data, and a timeout.  The timeout prevents the app from hanging indefinitely if the API is unresponsive.
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        
        result = response.json() # Parses the JSON response from the API.
        logger.info(f"Received response: {str(result)[:100]}...")

        if "reply" in result:
            return result["reply"].strip()
        else:
            logger.warning(f"Unexpected response format from API: {result}")
            return "⚠️ Error: Could not parse the model's response from API."

    except requests.exceptions.Timeout: # Handles a timeout error specifically.
        logger.error(f"Request to {MODEL_API_URL} timed out.")
        return "⚠️ Error: The request to the model API timed out."
    except requests.exceptions.RequestException as e: # Handles general request exceptions (connection errors, etc.)
        logger.error(f"Error calling model API at {MODEL_API_URL}: {e}")
        return f"⚠️ Error: Could not reach the model service ({e})."
    except json.JSONDecodeError: # Handles errors in decoding the JSON response.
        logger.error(f"Failed to decode JSON response from {MODEL_API_URL}")
        return "⚠️ Error: Invalid response format from the model API."
    # These different `except` blocks provide more specific error messages for better debugging and user experience.
