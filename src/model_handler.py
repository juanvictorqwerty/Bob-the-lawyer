from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, StoppingCriteriaList, StoppingCriteria
import torch
from peft import PeftModel # Import PeftModel
from pathlib import Path

# System prompt
SYSTEM_PROMPT = "Respond conversationally and concisely. Do not make any conversation examples"

# Define the Hugging Face model identifier
# Replace this with the specific TinyLlama model you want to use from the Hub
BASE_MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0" # Base model
ADAPTER_ID = "juanvic/tinyllama-cameroon-law-lora"    # Your fine-tuned adapter

try:
    # Load tokenizer from the base model
    # local_files_only=False (default) will download if not cached
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    
    # Load the base model
    base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID)
    print(f"Base model '{BASE_MODEL_ID}' loaded successfully from Hugging Face Hub or cache.")

    # Load the LoRA adapter and apply it to the base model
    model = PeftModel.from_pretrained(base_model, ADAPTER_ID)
    print(f"Adapter '{ADAPTER_ID}' loaded and applied to the base model.")

except Exception as e:
    print(f"Error loading model '{BASE_MODEL_ID}' or adapter '{ADAPTER_ID}' from Hugging Face Hub: {str(e)}")
    # This is a critical error for the app's functionality.
    # Ensure you have an internet connection and the model ID is correct.
    raise RuntimeError(
        f"Failed to load base model '{BASE_MODEL_ID}' or adapter '{ADAPTER_ID}' from Hugging Face Hub. "
        "Please check your internet connection and the model identifier. "
        "If running in a restricted environment, ensure it can access huggingface.co. "
        f"Original error: {e}"
    )
# Check and set device
device = 0 if torch.cuda.is_available() else -1
print(f"Using {'CUDA' if device == 0 else 'CPU'} for inference")

# Initialize the pipeline
chat_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device=device,
)

# Define stopping criteria
class StopOnTokens(StoppingCriteria):
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        stop_tokens = [
            tokenizer.convert_tokens_to_ids("."),
            tokenizer.convert_tokens_to_ids("?"),
            tokenizer.convert_tokens_to_ids("!"),
            tokenizer.convert_tokens_to_ids("\n"),
            tokenizer.eos_token_id,
        ]
        return input_ids[0][-1].item() in stop_tokens  

# Chat generation function
def generate_reply(user_input: str,
                    max_new_tokens: int = 100,
                    temperature: float = 0.7,
                    top_p: float = 0.9) -> str:
    """
    Generates a chat-style reply using the pre-built text-generation pipeline.

    Args:
        user_input (str): The user's message.
        max_new_tokens (int): Max tokens to generate.
        temperature (float): Sampling temperature.
        top_p (float): Nucleus sampling probability.

    Returns:
        str: The assistant's reply.
    """
    # Construct the prompt
    prompt = (
        f"<|system|> {SYSTEM_PROMPT}\n"
        f"<|user|> {user_input}\n"
        f"<|assistant|>"
    )

    # Generate response
    outputs = chat_pipeline(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=temperature,
        top_p=top_p,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        stopping_criteria=StoppingCriteriaList([StopOnTokens()]),
        repetition_penalty=1.2,
    )

    # Extract and return the assistant's response
    return outputs[0]['generated_text'].split("<|assistant|>")[-1].strip()
