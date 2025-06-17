from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Ensure you have authenticated if necessary, though loading public models doesn't require it
# from huggingface_hub import notebook_login
# notebook_login() # Only needed for private repos or if you are pushing changes

# Replace with your specific repository ID
repo_id = "juanvic/Bob-tinyllma-law-lora"

# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained(repo_id)

# Load the model
# If you used quantization during training, you might need to specify the same quantization config
# when loading, or load it in full precision depending on your use case.
# For the PEFT LoRA model, you'll typically load the base model and then the PEFT weights.

# First, load the base model
base_model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0" # Your original base model

# If you trained with quantization, you might need to load the base model with it too
# from transformers import BitsAndBytesConfig
# bnb_config = BitsAndBytesConfig(
#     load_in_4bit=True,
#     bnb_4bit_use_double_quant=True,
#     bnb_4bit_quant_type="nf4",
#     bnb_4bit_compute_dtype=torch.bfloat16
# )
# base_model = AutoModelForCausalLM.from_pretrained(base_model_id, quantization_config=bnb_config, device_map="auto")

# If you trained without quantization on the base model (less likely for TinyLlama 1.1B),
# or just want to load the base model normally before applying PEFT weights:
base_model = AutoModelForCausalLM.from_pretrained(base_model_id, device_map="auto")


# Then, load the PEFT model from your repo
from peft import PeftModel

model = PeftModel.from_pretrained(base_model, repo_id)

# Merge the LoRA weights into the base model (optional, makes inference simpler)
# model = model.merge_and_unload() # Use this if you want a merged model for deployment

# Now 'model' is your fine-tuned model ready for inference
print("Model and tokenizer loaded successfully from Hugging Face Hub!")

# Example of how to use the model for inference:
# prompt = "What is the legal age of marriage in Cameroon?"
# inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
# outputs = model.generate(**inputs, max_new_tokens=100)
# print(tokenizer.decode(outputs[0], skip_special_tokens=True))