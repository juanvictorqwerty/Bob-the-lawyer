from transformers import AutoModelForCausalLM, AutoTokenizer
import os

model_name = "microsoft/phi-3-mini-4k-instruct"  # Replace with your model

# Download model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Save locally
save_dir = "C:/Program Files/Bob-the-lawyer-model/phi-3-local"

# Create parent directories if they don't exist
os.makedirs(save_dir, exist_ok=True)  # This creates all necessary parent directories

model.save_pretrained(save_dir)
tokenizer.save_pretrained(save_dir)

print(f"Model saved to {save_dir}")