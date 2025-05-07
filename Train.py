import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import load_dataset
from torch.nn import CrossEntropyLoss

# Configuration
MODEL_PATH = r"C:\Program Files\Bob-the-lawyer-model\tinyllama_model"
DATASET_PATH = r"C:\Users\JUAN MIKE\Desktop\Bob-the-lawyer\Bob-the-lawyer\train_suite\CameroonLaw.txt"
OUTPUT_DIR = r"D:\tinyllama_finetuned"
BATCH_SIZE = 2
EPOCHS = 3
LEARNING_RATE = 5e-5
MAX_LENGTH = 128

# 1. Chargement du modèle et tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 2. Préparation des données
def prepare_dataset(file_path):
    dataset = load_dataset("text", data_files={"train": file_path})
    
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
            return_tensors="pt"
        )
    
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    tokenized_datasets = tokenized_datasets["train"]
    
    # Ajout des labels
    tokenized_datasets = tokenized_datasets.map(
        lambda examples: {'labels': examples['input_ids']},
        batched=True
    )
    
    return tokenized_datasets

dataset = prepare_dataset(DATASET_PATH)

# 3. Classe Trainer personnalisée corrigée
class CustomTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        
        # Décalage des logits et labels
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()
        
        loss_fct = CrossEntropyLoss()
        loss = loss_fct(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1)
        )
        
        return (loss, outputs) if return_outputs else loss

# 4. Arguments d'entraînement
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    overwrite_output_dir=True,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    learning_rate=LEARNING_RATE,
    save_steps=500,
    save_total_limit=2,
    logging_dir='./logs',
    logging_steps=100,
    fp16=False,
    gradient_accumulation_steps=4,
    remove_unused_columns=False,  # Important pour garder les labels
    dataloader_pin_memory=False,  # Désactivé pour CPU
)

# 5. Entraînement
trainer = CustomTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

print("Début du fine-tuning...")
trainer.train()
print("Fine-tuning terminé!")

# 6. Sauvegarde
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)