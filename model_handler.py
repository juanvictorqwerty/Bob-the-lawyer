from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os

# Local model path (Windows-safe)
MODEL_PATH = r"C:\Program Files\Bob-the-lawyer-model\tinyllama_model"

print("⏳ Loading TinyLLaMA from local path...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)

# Use CUDA if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()
print(f"✅ Model loaded on: {device}")

def generate_reply(prompt, max_new_tokens=200):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=0.2,
            top_p=0.5,
            pad_token_id=tokenizer.eos_token_id
        )
    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return reply[len(prompt):].strip()
