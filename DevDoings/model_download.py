from peft import PeftModel
from transformers import AutoModelForCausalLM

# Load the base model
base_model = AutoModelForCausalLM.from_pretrained("microsoft/phi-1_5")

# Load the PEFT adapter
model = PeftModel.from_pretrained(base_model, "juanvic/Bob-law-phi")

# Merge the adapter with the base model and unload the adapter
merged_model = model.merge_and_unload()

# Now you can use merged_model as a regular model
# You might want to save it:
merged_model.save_pretrained("merged_model")