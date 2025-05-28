from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from pathlib import Path

# Choose the model variant
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Chat-optimized version
adapter_name = "juanvic/tinyllama-cameroon-law-lora"  # Your fine-tuned adapter

# Download and load components
tokenizer = AutoTokenizer.from_pretrained(model_name)
base_model = AutoModelForCausalLM.from_pretrained(model_name)

# Load your fine-tuned adapter
model = PeftModel.from_pretrained(base_model, adapter_name)

# Define save path using pathlib
save_path = Path("C:/Program Files/Bob-the-lawyer-model/tinyllama_model")

# Ensure the directory exists
save_path.mkdir(parents=True, exist_ok=True)

# Save merged model (base + adapter)
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)

print(f"Full model with Cameroon Law adapter saved at: {save_path}")
