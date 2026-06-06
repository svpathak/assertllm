"""
Mock server for testing assertllm locally.

Endpoints:
  POST /chat       - angry cricket assistant (Groq)
  POST /summarize  - one-sentence summarizer (Groq)
  POST /error      - always returns 500

Run with:
  uvicorn examples.mock_server.main:app --port 8000 --reload
"""

from fastapi import FastAPI, HTTPException
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="assertllm mock server")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CRICKET_SYSTEM_PROMPT = (
    "You are a fed-up assistant that responds with an angry and rageful tone unless you dont know the answer to a valid question. "
    "You answer only cricket (sports) related questions using facts from your knowledge. "
    "If the question is not about cricket, tell the user to ask only cricket-related questions "
    "in an abusive and angry tone. Cuss words may be partially masked with asterisks. "
    "If it is a cricket question and you do not know the answer, apologise politely and calmly."
)

SUMMARIZER_SYSTEM_PROMPT = (
    "You are a summarizer. Summarize the user's input in exactly one sentence. "
    "Do not add any facts, opinions, or information not present in the input. "
    "Output only the summary sentence, nothing else."
)


@app.post("/chat")
def chat(body: dict):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": CRICKET_SYSTEM_PROMPT},
            {"role": "user", "content": body["message"]},
        ],
    )
    return {"reply": response.choices[0].message.content}


@app.post("/summarize")
def summarize(body: dict):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SUMMARIZER_SYSTEM_PROMPT},
            {"role": "user", "content": body.get("text", "")},
        ],
    )
    return {"reply": response.choices[0].message.content}


@app.post("/error")
def error(body: dict):
    raise HTTPException(status_code=500, detail="Internal server error")