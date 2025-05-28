from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, StoppingCriteriaList, StoppingCriteria
import torch
from pathlib import Path

# System prompt
SYSTEM_PROMPT = "Respond conversationally and concisely. Do not make any conversation examples"

# Define model path using pathlib
# Cross-platform model paths (checks local directory first, then standard locations)
MODEL_PATHS = [
    Path("Bob-the-lawyer-model/tinyllama_model"),  # Local directory
    Path.home() / "Bob-the-lawyer-model/tinyllama_model",  # User home directory
    Path.home() / "Documents/Bob-the-lawyer-model/tinyllama_model",  # Windows/Mac Documents
    Path.home() / ".local/share/Bob-the-lawyer-model/tinyllama_model",  # Linux standard data location
]

# Try loading model from first existing path
for model_path in MODEL_PATHS:
    if model_path.exists():
        try:
            tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
            model = AutoModelForCausalLM.from_pretrained(str(model_path), local_files_only=True)
            print(f"Model loaded successfully from: {model_path}")
            break
        except Exception as e:
            print(f"Error loading model from {model_path}: {str(e)}")
            continue
else:
    raise FileNotFoundError(
        "Model not found in any of these locations:\n" + 
        "\n".join(f"- {p}" for p in MODEL_PATHS) +
        "\nPlease ensure the model files are in one of these paths."
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
