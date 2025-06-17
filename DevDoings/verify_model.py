from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def verify_transformers_model(model_path: str):
    """Verify that the model is properly saved and loadable"""
    try:
        # Test loading
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path)
        
        # Test inference
        test_input = "What is contract law?"
        inputs = tokenizer(test_input, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"✅ Model verification successful!")
        print(f"Test response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Model verification failed: {e}")
        return False

# Verify your fine-tuned model
verify_transformers_model("./bob-lawyer-finetuned")