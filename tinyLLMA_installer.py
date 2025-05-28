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

MODEL_PATHS = [
    Path("Bob-the-lawyer-model/tinyllama_model"),  # Local directory - Option 1
    Path.home() / "Bob-the-lawyer-model/tinyllama_model",  # User home directory - Option 2
    Path.home() / "Documents/Bob-the-lawyer-model/tinyllama_model",  # Windows/Mac Documents - Option 3
    Path.home() / ".local/share/Bob-the-lawyer-model/tinyllama_model",  # Linux standard data location - Option 4
]

# Display path options to the user
print("Please select a path option:")
for i, path in enumerate(MODEL_PATHS, start=1):
    print(f"{i}. {path}")

# Get user input
while True:
    try:
        choice = int(input("Enter your choice (1-4): "))
        if 1 <= choice <= 4:
            selected_path = MODEL_PATHS[choice - 1]
            break
        else:
            print("Please enter a number between 1 and 4.")
    except ValueError:
        print("Please enter a valid number.")

# Define save path using pathlib
save_path = selected_path

# Ensure the directory exists
save_path.mkdir(parents=True, exist_ok=True)

print(f"Selected path: {save_path}")

# Save merged model (base + adapter)
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)

print(f"Full model with Cameroon Law adapter saved at: {save_path}")
