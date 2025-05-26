from transformers import AutoModelForCausalLM, AutoTokenizer

# This is the full path to your local TinyLLaMA model
MODEL_PATH = "C:/Users/royce/Documents/Bob-the-lawyer-model/tinyllama_model"

# Load the tokenizer and model locally without trying to download from Hugging Face
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, local_files_only=True)

# Example function to generate a reply (if needed)
def generate_reply(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=100)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)