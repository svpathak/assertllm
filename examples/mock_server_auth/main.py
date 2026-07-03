"""
Mock server for testing assertllm's env var / auth resolution.

Each endpoint expects auth in a different place. All endpoints check
against the same expected secret, read from MOCK_AUTH_TOKEN in .env.

Endpoints:
  POST /auth/bearer    - expects "Authorization: Bearer <token>" header
  POST /auth/apikey    - expects "X-API-Key: <token>" header
  POST /auth/query     - expects "?api_key=<token>" query parameter
  POST /auth/body      - expects {"api_key": "<token>", ...} in body
  POST /auth/basic     - expects "Authorization: Basic <base64(user:token)>" header

Each returns:
  200 {"reply": "authorized"}        if auth matches
  401 {"detail": "unauthorized"}     if auth missing or wrong

Run with:
  uvicorn examples.mock_server_auth.main:app --port 8001 --reload
"""

import base64
import os
from fastapi import FastAPI, Header, HTTPException, Query, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="assertllm mock auth server")

EXPECTED_TOKEN = os.getenv("EXPECTED_AUTH_TOKEN", "")
EXPECTED_USER = os.getenv("EXPECTED_AUTH_USER", "assertllm")


def _ok():
    return {"reply": "authorized"}


def _unauthorized():
    raise HTTPException(status_code=401, detail="unauthorized")


@app.post("/auth/bearer")
def auth_bearer(authorization: str | None = Header(default=None)):
    if not authorization or authorization != f"Bearer {EXPECTED_TOKEN}":
        _unauthorized()
    return _ok()


@app.post("/auth/apikey")
def auth_apikey(x_api_key: str | None = Header(default=None)):
    if not x_api_key or x_api_key != EXPECTED_TOKEN:
        _unauthorized()
    return _ok()


@app.post("/auth/query")
def auth_query(api_key: str | None = Query(default=None)):
    if not api_key or api_key != EXPECTED_TOKEN:
        _unauthorized()
    return _ok()


@app.post("/auth/body")
async def auth_body(request: Request):
    body = await request.json()
    if body.get("api_key") != EXPECTED_TOKEN:
        _unauthorized()
    return _ok()


@app.post("/auth/basic")
def auth_basic(authorization: str | None = Header(default=None)):
    expected = "Basic " + base64.b64encode(f"{EXPECTED_USER}:{EXPECTED_TOKEN}".encode()).decode()
    if not authorization or authorization != expected:
        _unauthorized()
    return _ok()