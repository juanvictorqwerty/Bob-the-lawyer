from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, StoppingCriteriaList, StoppingCriteria
from peft import PeftModel
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Model Configuration ---
SYSTEM_PROMPT = "Respond conversationally and concisely. Do not make any conversation examples"
BASE_MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
ADAPTER_ID = "juanvic/tinyllama-cameroon-law-lora"

# --- Global variables for model and tokenizer ---
chat_pipeline_global = None
tokenizer_global = None

class StopOnTokens(StoppingCriteria):
    def __init__(self, tokenizer_ref):
        self.tokenizer_ref = tokenizer_ref

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        # Ensure eos_token_id is not None before trying to use it
        eos_token_id = self.tokenizer_ref.eos_token_id if self.tokenizer_ref.eos_token_id is not None else -1 # Use a dummy if None
        stop_tokens_ids = [
            self.tokenizer_ref.convert_tokens_to_ids("."),
            self.tokenizer_ref.convert_tokens_to_ids("?"),
            self.tokenizer_ref.convert_tokens_to_ids("!"),
            self.tokenizer_ref.convert_tokens_to_ids("\n"),
            eos_token_id,
        ]
        return input_ids[0][-1].item() in stop_tokens_ids

def load_model():
    global chat_pipeline_global, tokenizer_global
    try:
        logger.info(f"Loading tokenizer for base model: {BASE_MODEL_ID}")
        tokenizer_global = AutoTokenizer.from_pretrained(BASE_MODEL_ID)

        logger.info(f"Loading base model: {BASE_MODEL_ID}")
        base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID)
        logger.info(f"Base model '{BASE_MODEL_ID}' loaded successfully.")

        logger.info(f"Loading and applying adapter: {ADAPTER_ID}")
        model = PeftModel.from_pretrained(base_model, ADAPTER_ID)
        logger.info(f"Adapter '{ADAPTER_ID}' loaded and applied to the base model.")

        device_num = 0 if torch.cuda.is_available() else -1
        device_name = "CUDA" if device_num == 0 else "CPU"
        logger.info(f"Using {device_name} for inference.")

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
        raise RuntimeError(f"Failed to load model components: {e}")

app = FastAPI(
    title="Lawyer Bot API",
    description="API for generating legal chat responses.",
    version="1.0.0",
    on_startup=[load_model] # Load model on startup
)

class GenerationRequest(BaseModel):
    user_input: str
    max_new_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 0.9

class GenerationResponse(BaseModel):
    reply: str


@app.post("/", response_model=GenerationResponse)
async def generate_chat_reply(request: GenerationRequest):
    if chat_pipeline_global is None or tokenizer_global is None:
        logger.error("Pipeline or tokenizer not initialized.")
        raise HTTPException(status_code=503, detail="Model service is not ready. Please try again later.")
    try:
        prompt = (
            f"<|system|> {SYSTEM_PROMPT}\n"
            f"<|user|> {request.user_input}\n"
            f"<|assistant|>"
        )

        # Run the synchronous pipeline in a thread pool to avoid blocking the event loop
        outputs = await run_in_threadpool(
            chat_pipeline_global,
            prompt,
            max_new_tokens=request.max_new_tokens,
            do_sample=True,
            temperature=request.temperature,
            top_p=request.top_p,
            pad_token_id=tokenizer_global.eos_token_id,
            eos_token_id=tokenizer_global.eos_token_id,
            stopping_criteria=StoppingCriteriaList([StopOnTokens(tokenizer_global)]),
            repetition_penalty=1.2,
        )
        reply_text = outputs[0]['generated_text'].split("<|assistant|>")[-1].strip()
        return GenerationResponse(reply=reply_text)
    except Exception as e:
        logger.error(f"Error during text generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")
if __name__ == "__main__":
    import uvicorn
    # It's recommended to run Uvicorn from the command line for more options:
    # uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=os.getenv("PORT", 7860))
