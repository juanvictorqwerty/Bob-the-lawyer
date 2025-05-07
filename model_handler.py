from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

# System prompt
SYSTEM_PROMPT = "Respond conversationally and concisely. Do not make any conversation examples"

# Pre-load tokenizer and model globally
MODEL_PATH = r"C:\Program Files\Bob-the-lawyer-model\tinyllama_model"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)

# Initialize the pipeline once
device = 0 if torch.cuda.is_available() else -1
chat_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device=device,
)

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
    )
    
    # Extract and return the assistant's response
    return outputs[0]['generated_text'].split("<|assistant|>")[-1].strip()