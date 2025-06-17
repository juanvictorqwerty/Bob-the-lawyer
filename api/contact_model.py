from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import torch
from transformers import (
    pipeline, AutoTokenizer, AutoModelForCausalLM,
    StoppingCriteriaList, StoppingCriteria
)
from peft import PeftModel, PeftConfig
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a legal assistant. Provide accurate, concise responses to legal queries."
BASE_MODEL_ID = "microsoft/phi-1_5"
ADAPTER_ID = "juanvic/Bob-law-phi"

chat_pipeline_global = None
tokenizer_global = None

class StopOnTokens(StoppingCriteria):
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.stop_ids = {
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("."),
            tokenizer.convert_tokens_to_ids("?"),
        }

    def __call__(self, input_ids, scores, **kwargs):
        return input_ids[0, -1].item() in self.stop_ids

def load_model():
    global chat_pipeline_global, tokenizer_global
    adapter_config = PeftConfig.from_pretrained(ADAPTER_ID)
    logger.info(f"Adapter config loaded.")

    tokenizer_global = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    tokenizer_global.pad_token = tokenizer_global.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
    )
    logger.info("Base model loaded in float16.")

    model = PeftModel.from_pretrained(base_model, ADAPTER_ID, torch_dtype=torch.float16)
    model = model.merge_and_unload()
    logger.info("Adapter merged into base model.")

    chat_pipeline_global = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer_global,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    logger.info("Pipeline ready for inference.")

app = FastAPI(on_startup=[load_model])

class GenerationRequest(BaseModel):
    user_input: str
    max_new_tokens: int = 60
    temperature: float = 0.7
    top_p: float = 0.9

class GenerationResponse(BaseModel):
    reply: str

@app.post("/", response_model=GenerationResponse)
async def chat(request: GenerationRequest):
    if chat_pipeline_global is None:
        raise HTTPException(status_code=503, detail="Model is loading, please retry shortly.")

    prompt = (
        f"<|system|>{SYSTEM_PROMPT}</s>"
        f"<|user|>{request.user_input.strip()}</s>"
        "<|assistant|>"
    )

    stop_criteria = StoppingCriteriaList([StopOnTokens(tokenizer_global)])
    
    try:
        outputs = await run_in_threadpool(
            chat_pipeline_global,
            prompt,
            max_new_tokens=request.max_new_tokens,
            do_sample=True,
            temperature=request.temperature,
            top_p=request.top_p,
            pad_token_id=tokenizer_global.eos_token_id,
            eos_token_id=tokenizer_global.eos_token_id,
            stopping_criteria=stop_criteria
        )
    except Exception as e:
        logger.error("Generation failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    text = outputs[0]["generated_text"]
    reply = text.split("<|assistant|>")[-1].split("</s>")[0].strip()
    return GenerationResponse(reply=reply)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 7860)))
