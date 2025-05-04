from transformers import AutoTokenizer, AutoModelForCausalLM

# Choose one of these TinyLlama variants:
# model_name = "PY007/TinyLlama-1.1B-step-50K-105b"  # Base 1.1B parameter model
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"    # Chat-optimized version

# Download and load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Save the model and tokenizer locally (optional)
save_path = "C:/Program Files/Bob-the-lawyer-model/tinyllama_model"
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)

print(f"TinyLlama model and tokenizer saved at: {save_path}")