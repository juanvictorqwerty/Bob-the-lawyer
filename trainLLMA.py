from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model, TaskType

# === Load TinyLLaMA and tokenizer ===
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", load_in_8bit=True)

# === Apply LoRA ===
peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    inference_mode=False,
    r=8,
    lora_alpha=32,
    lora_dropout=0.1
)
model = get_peft_model(model, peft_config)

# === Load and tokenize dataset ===
dataset = load_dataset("text", data_files={"train": "cameroon_law.txt"})

def tokenize_function(example):
    return tokenizer(example["text"], truncation=True, padding="max_length", max_length=512)

tokenized = dataset.map(tokenize_function, batched=True, remove_columns=["text"])

# === Data collator ===
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

# === Training configuration ===
training_args = TrainingArguments(
    output_dir="./tinyllama-cameroon-law-lora",
    per_device_train_batch_size=4,
    num_train_epochs=3,
    save_steps=100,
    logging_steps=10,
    fp16=True,
    save_total_limit=2,
    report_to="none"
)

# === Trainer ===
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    tokenizer=tokenizer,
    data_collator=data_collator
)

# === Train ===
trainer.train()

# === Save ===
model.save_pretrained("tinyllama-cameroon-law-lora")
tokenizer.save_pretrained("tinyllama-cameroon-law-lora")
