"""
Mock server for testing assertllm locally.

Endpoints:
  POST /chat        - returns a refund policy response (passing case)
  POST /chat/fail   - returns a bad response (failing case)
  POST /summarize   - returns a summary response (passing case)
  POST /error       - always returns 500 (error case)

Run with:
  uvicorn examples.mock_server.main:app --port 8000 --reload
"""

from fastapi import FastAPI, HTTPException

app = FastAPI(title="assertllm mock server")


@app.post("/chat")
def chat(body: dict):
    message = body.get("message", "").lower()
    if "return" in message or "refund" in message:
        return {
            "reply": (
                "Thank you for reaching out! We offer a 30-day return window "
                "on all purchases. Simply bring your receipt to any store location "
                "and we will process your return promptly."
            )
        }
    return {"reply": "I am not sure how to help with that. Please contact support."}


@app.post("/chat/fail")
def chat_fail():
    return {
        "reply": (
            "Returns are handled by our team. "
            "Call us at 555-123-4567 for assistance."
        )
    }


@app.post("/summarize")
def summarize():
    return {
        "reply": "Quarterly earnings exceeded expectations by 12%."
    }


@app.post("/error")
def error():
    raise HTTPException(status_code=500, detail="Internal server error")