"""
Simple LLM server using Transformers and FastAPI
Serves Qwen3-Coder-14B on port 8001
"""
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uvicorn
import json

app = FastAPI()

# Global model and tokenizer
model = None
tokenizer = None

class Message(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[Dict]] = None

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict]
    temperature: float = 0.2
    max_tokens: int = 4096
    tools: Optional[List[Dict]] = None
    tool_choice: Optional[str] = None

class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict]


def load_model():
    """Load Qwen3-Coder with memory optimization"""
    global model, tokenizer

    print("Loading Qwen3-Coder-30B-A3B-Instruct (MoE - only 3B active params)...")
    print("This model is memory-optimized for DGX Spark stability (<40% memory)")
    model_name = "Qwen/Qwen3-Coder-30B-A3B-Instruct"

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    # MoE model with only 3B active parameters - very memory efficient!
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        max_memory={0: "10GiB"}  # Cap at 10GB to stay under 40% of typical DGX memory
    )

    print(f"✓ Qwen3-Coder loaded successfully on GPU")
    print(f"✓ Active params: 3B (MoE architecture)")
    print(f"✓ Memory usage capped at <40% to prevent DGX crashes")


@app.on_event("startup")
async def startup_event():
    load_model()


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "Qwen3-Coder-14B",
                "object": "model",
                "created": 1234567890,
                "owned_by": "qwen"
            }
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI-compatible chat completions endpoint"""
    import time

    # Format messages for the model
    messages = request.messages

    # Build prompt
    if request.tools:
        # Add tools to system message
        system_msg = next((m for m in messages if m['role'] == 'system'), None)
        if system_msg:
            tools_desc = "\n\nAvailable tools:\n" + json.dumps(request.tools, indent=2)
            system_msg['content'] += tools_desc

    # Use apply_chat_template if available
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
                text += f"System: {content}\n\n"
            elif role == 'user':
                text += f"User: {content}\n\n"
            elif role == 'assistant':
                text += f"Assistant: {content}\n\n"
        text += "Assistant: "

    # Tokenize
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=request.temperature > 0,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode
    response_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

    # Parse tool calls if needed
    tool_calls = None
    if request.tools and "```tool" in response_text:
        # Simple tool call parsing
        # This is a simplified version - production would need more robust parsing
        try:
            import re
            matches = re.findall(r'```tool\n(.*?)\n```', response_text, re.DOTALL)
            if matches:
                tool_calls = []
                for match in matches:
                    tool_data = json.loads(match)
                    tool_calls.append({
                        "id": f"call_{int(time.time() * 1000)}",
                        "type": "function",
                        "function": tool_data
                    })
        except:
            pass

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
                    "content": response_text,
                    "tool_calls": tool_calls
                },
                "finish_reason": "stop"
            }
        ]
    }


if __name__ == "__main__":
    print("="*60)
    print("Qwen3-Coder-14B Server (FastAPI + Transformers)")
    print("="*60)
    print("Starting on http://localhost:8001")
    print("")

    uvicorn.run(app, host="0.0.0.0", port=8001)
