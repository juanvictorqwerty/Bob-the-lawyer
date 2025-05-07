# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM



# Download and load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("openai-community/gpt2")
model = AutoModelForCausalLM.from_pretrained("openai-community/gpt2")

# Save the model and tokenizer locally (optional)
save_path = "C:/Program Files/Bob-the-lawyer-model/gpt2_model"
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)

print(f"TinyLlama model and tokenizer saved at: {save_path}")