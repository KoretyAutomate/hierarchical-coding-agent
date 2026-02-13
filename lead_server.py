"""
Project Lead Server
Serves via FastAPI + Transformers for deep research and planning.
Configure MODEL_NAME below or via LEAD_SERVER_MODEL env var.
"""
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn

app = FastAPI()

# Global model and tokenizer
model = None
tokenizer = None

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict]
    temperature: float = 0.3
    max_tokens: int = 4096

@app.on_event("startup")
async def load_model():
    """Load Qwen3-Thinking model on startup"""
    global model, tokenizer

    model_name = os.environ.get("LEAD_SERVER_MODEL", "Qwen/Qwen2.5-32B-Instruct-AWQ")

    print("="*60)
    print("Loading Project Lead Model")
    print("="*60)
    print(f"Model: {model_name}")
    print("Purpose: Deep research, planning, decision-making")
    print("")

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=True
        # AWQ 4-bit quantization keeps memory usage low automatically
    )

    print(f"✓ Project Lead loaded successfully")
    print(f"✓ Device: {model.device}")
    print(f"✓ AWQ 4-bit quantization active (low memory usage)")
    print("")

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "project-lead",
                "object": "model",
                "created": 1234567890,
                "owned_by": "local"
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI-compatible chat completions endpoint"""
    import time

    messages = request.messages

    # Use apply_chat_template for proper formatting
    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
    except:
        # Fallback to simple concatenation
        text = ""
        for msg in messages:
            role = msg['role']
            content = msg['content']
            if role == 'system':
                text += f"<|system|>\n{content}\n\n"
            elif role == 'user':
                text += f"<|user|>\n{content}\n\n"
            elif role == 'assistant':
                text += f"<|assistant|>\n{content}\n\n"
        text += "<|assistant|>\n"

    # Tokenize
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=request.temperature > 0,
            pad_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.05
        )

    # Decode
    response_text = tokenizer.decode(
        outputs[0][inputs.input_ids.shape[1]:],
        skip_special_tokens=True
    )

    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_name": os.environ.get("LEAD_SERVER_MODEL", "Qwen/Qwen2.5-32B-Instruct-AWQ")
    }

if __name__ == "__main__":
    print("="*60)
    print("Project Lead Server")
    print("="*60)
    print("Starting on http://localhost:8000")
    print("OpenAI-compatible API at /v1/chat/completions")
    print("")

    uvicorn.run(app, host="0.0.0.0", port=8000)
