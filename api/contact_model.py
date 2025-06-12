from fastapi import FastAPI, HTTPException  # Used to create the API and handle HTTP errors.
from fastapi.concurrency import run_in_threadpool  # Used to run synchronous tasks in a separate thread, optimizing performance.
from pydantic import BaseModel  # Used for data validation and settings management using Python type annotations.
import torch  # PyTorch library, used here for tensor operations and GPU support if available.
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, StoppingCriteriaList, StoppingCriteria  # Hugging Face Transformers library for NLP tasks, model loading, and tokenization.
from peft import PeftModel  # Performance Efficient Fine-tuning (PEFT) library for applying adapters like LoRA to models.
import logging  # Standard Python library for logging events.
import os  # Standard Python library for interacting with the operating system, e.g., environment variables.

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) #create a session

# --- Model Configuration ---: Defines essential parameters for the model.
# The system prompt sets the behavior of the assistant.
# BASE_MODEL_ID specifies the pre-trained language model to use.
# ADAPTER_ID points to the location of the fine-tuned adapter.
SYSTEM_PROMPT = "Respond conversationally and concisely. Do not make any conversation examples.Do not put dates"
BASE_MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
ADAPTER_ID = "juanvic/tinyllama-cameroon-law-lora"

# --- Global variables for model and tokenizer ---: Declares global variables to hold the loaded model and tokenizer for reuse.
chat_pipeline_global = None
tokenizer_global = None

class StopOnTokens(StoppingCriteria):
    """
    Defines a custom stopping criterion for text generation.  The generation will stop
    when certain tokens (like sentence terminators) are encountered.
    """
    def __init__(self, tokenizer_ref):
        # Stores a reference to the tokenizer to access its properties like eos_token_id.
        self.tokenizer_ref = tokenizer_ref

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        """
        Evaluates whether the generation should stop based on the last generated token.
        This method is called at each generation step.
        """
        # Ensure eos_token_id is not None before trying to use it
        eos_token_id = self.tokenizer_ref.eos_token_id if self.tokenizer_ref.eos_token_id is not None else -1 # Use a dummy if None
        stop_tokens_ids = [
            self.tokenizer_ref.convert_tokens_to_ids("."),
            self.tokenizer_ref.convert_tokens_to_ids("?"),
            self.tokenizer_ref.convert_tokens_to_ids("!"),
            self.tokenizer_ref.convert_tokens_to_ids("\n"),
            eos_token_id,
        ]
        # Returns True if the last generated token is one of the stop tokens, signaling the generation to halt.
        return input_ids[0][-1].item() in stop_tokens_ids

def load_model():
    """
    Loads the tokenizer, base model, and applies the adapter. Initializes the text
    generation pipeline. Handles potential errors during loading.
    """
    global chat_pipeline_global, tokenizer_global
    # This function is designed to be called once at startup to initialize the model and tokenizer.
    try:
        logger.info(f"Loading tokenizer for base model: {BASE_MODEL_ID}")
        tokenizer_global = AutoTokenizer.from_pretrained(BASE_MODEL_ID)

        logger.info(f"Loading base model: {BASE_MODEL_ID}")
        base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID)
        logger.info(f"Base model '{BASE_MODEL_ID}' loaded successfully.")

        logger.info(f"Loading and applying adapter: {ADAPTER_ID}")
        model = PeftModel.from_pretrained(base_model, ADAPTER_ID)
        logger.info(f"Adapter '{ADAPTER_ID}' loaded and applied to the base model.")

        # Determine if CUDA (GPU) is available and set the device accordingly.
        device_num = 0 if torch.cuda.is_available() else -1
        device_name = "CUDA" if device_num == 0 else "CPU"
        logger.info(f"Using {device_name} for inference.")

        # Initialize the text generation pipeline with the loaded model, tokenizer, and device.
        chat_pipeline_global = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer_global,
            device=device_num,
        )
        logger.info("Text generation pipeline initialized successfully.")

    except Exception as e:
        logger.error(f"Error loading model or pipeline: {e}", exc_info=True)
        # If model loading fails, the app shouldn't start or should indicate a critical error.
        # Raising RuntimeError will typically stop the application from starting if this occurs during startup.
        raise RuntimeError(f"Failed to load model components: {e}")

app = FastAPI( # Creates the FastAPI application instance. The on_startup event is used to load the model when the application starts.
    title="Lawyer Bot API",
    description="API for generating legal chat responses.",
    version="1.0.0",
    on_startup=[load_model] # Load model on startup
)

class GenerationRequest(BaseModel):
    """
    Pydantic model defining the expected structure of an incoming text generation request.
    Includes user input and optional parameters for generation.
    """
    user_input: str  # The input text from the user.
    max_new_tokens: int = 100  # Maximum number of new tokens to generate.
    temperature: float = 0.7  # Sampling temperature for generation (controls randomness).
    top_p: float = 0.9  # Nucleus sampling probability (controls diversity).

class GenerationResponse(BaseModel):
    """
    Pydantic model defining the structure of the response returned by the API.
    It contains the generated reply text.
    """
    reply: str


@app.post("/", response_model=GenerationResponse)
# Defines a POST endpoint at the root path ("/") that expects a GenerationRequest and returns a GenerationResponse.
async def generate_chat_reply(request: GenerationRequest):
    if chat_pipeline_global is None or tokenizer_global is None:
        # Check if the model and tokenizer have been initialized.
        logger.error("Pipeline or tokenizer not initialized.")
        # Raises an HTTPException if the model pipeline or tokenizer isn't initialized,
        # indicating the service isn't ready.
        # Returns a 503 Service Unavailable error to the client.
        # This typically suggests the server is temporarily unable to handle the request.
        # Clients might retry after a delay.

        raise HTTPException(status_code=503, detail="Model service is not ready. Please try again later.")
    try:
        # Construct the prompt in the format expected by the chat model.
        prompt = (
            f"<|system|> {SYSTEM_PROMPT}\n"
            f"<|user|> {request.user_input}\n"
            f"<|assistant|>"
        )

        # Run the synchronous pipeline in a thread pool to avoid blocking the event loop
        # Uses `run_in_threadpool` to execute the potentially long-running text generation
        # without blocking the main event loop of the FastAPI application. This ensures
        # the server remains responsive to other requests.
        outputs = await run_in_threadpool(
            chat_pipeline_global,
            # The first argument to run_in_threadpool should be the callable (the pipeline object itself can be called).
            prompt,  # Input prompt for text generation
            max_new_tokens=request.max_new_tokens,  # Maximum number of tokens to generate
            do_sample=True,  # Enable sampling for diverse outputs
            temperature=request.temperature,  # Controls randomness (higher = more random)
            top_p=request.top_p,  # Nucleus sampling (limits the pool of tokens to sample from)
            pad_token_id=tokenizer_global.eos_token_id,  # Use EOS token for padding (important for batching)
            eos_token_id=tokenizer_global.eos_token_id,  # Specify end-of-sequence token
            stopping_criteria=StoppingCriteriaList([StopOnTokens(tokenizer_global)]),  # Apply custom stopping criteria
            repetition_penalty=1.2,  # Penalize repeated tokens to encourage diverse outputs
        )
        # The pipeline returns a list of dictionaries; we take the first result.
        # The generated text includes the prompt, so we split by the assistant tag and take the last part.
        reply_text = outputs[0]['generated_text'].split("<|assistant|>")[-1].strip()

        # Extracts the generated reply from the pipeline output, removing the assistant tag.
        # The `strip()` method is used to remove any leading or trailing whitespace characters.
        # This ensures a clean, user-friendly response.
        return GenerationResponse(reply=reply_text)
    except Exception as e:
        logger.error(f"Error during text generation: {e}", exc_info=True)
        # Handles any exceptions that occur during the text generation process.
        # Logs the error with a traceback for detailed debugging information.
        # Raises an HTTPException with a 500 Internal Server Error to inform the client
        # that an unexpected error occurred on the server side.

        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")
if __name__ == "__main__":
    # This block executes if the script is run directly (e.g., `python contact_model.py`).
    import uvicorn
    # It's recommended to run Uvicorn from the command line for more options:
    # uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
    # The `os.getenv("PORT", 7860)` allows setting the port via an environment variable, defaulting to 7860.
    uvicorn.run(app, host="0.0.0.0", port=os.getenv("PORT", 7860))
