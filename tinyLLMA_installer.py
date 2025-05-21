from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Choose the model variant
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Chat-optimized version
adapter_name = "juanvic/tinyllama-cameroon-law-lora"  # Your fine-tuned adapter

# Download and load components
tokenizer = AutoTokenizer.from_pretrained(model_name)
base_model = AutoModelForCausalLM.from_pretrained(model_name)

# Load your fine-tuned adapter
model = PeftModel.from_pretrained(base_model, adapter_name)

# Save everything locally
save_path = "C:/Program Files/Bob-the-lawyer-model/tinyllama_model"

# Save merged model (base + adapter)
model.save_pretrained(save_path)  # This saves both config and adapter weights
tokenizer.save_pretrained(save_path)

print(f"Full model with Cameroon Law adapter saved at: {save_path}")