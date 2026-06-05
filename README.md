# assertllm

A CLI tool that fires inputs at an AI endpoint and evaluates outputs using plain-English behavioral assertions, judged by a second LLM.

The target user is an engineer who wired up an AI endpoint and needs a smoke test that runs in CI. No platform to learn. Just a YAML file and an exit code.

---

## How it works

```
User writes YAML config
       |
CLI reads config, validates it
       |
For each test:
  -> Fire input at endpoint, get raw response
  -> Pass all assertions to judge in one call
  -> Get pass/fail list back
  -> Collect results
       |
Print summary to terminal, exit 0 or 1
```

---

## Install

```bash
git clone https://github.com/svpathak/assertllm.git
cd assertllm

conda create -n py311 python=3.11
conda activate py311

pip install -e .
```

---

## Setup

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Only the key for your chosen judge provider is required.

---

## Config

```yaml
judge:
  provider: groq
  model: llama-3.3-70b-versatile

tests:
  - name: refund policy
    endpoint: https://your-api.com/chat
    method: POST
    headers:
      Authorization: Bearer ${MY_TOKEN}
    body:
      message: "What is your return policy?"
    assert:
      - mentions a 30-day return window
      - does not mention a phone number
      - tone is polite
```

API keys are never declared in the config -- they are read from `.env` based on the provider.

Supported judge providers: `groq`, `anthropic`, `openai`, `ollama`.

---

## Commands

Run all tests:
```bash
assertllm run config.yaml
```

Run a single test by name:
```bash
assertllm run config.yaml --test "refund policy"
```

Save a snapshot of current endpoint responses:
```bash
assertllm snapshot config.yaml
```

Compare current responses against the latest snapshot:
```bash
assertllm diff config.yaml
```

Compare against a specific snapshot:
```bash
assertllm diff config.yaml --snapshot snapshots/config_20250529_143022.json
```

List all saved runs (latest first):
```bash
assertllm inspect --list
```

List runs for a specific config only:
```bash
assertllm inspect --list --config examples/sample1.yaml
```

Inspect the latest run:
```bash
assertllm inspect
```

Inspect the latest run for a specific config:
```bash
assertllm inspect --config examples/sample1.yaml
```

Inspect a specific run file:
```bash
assertllm inspect --run runs/sample1_20250604_103500.json
```

Filter to a single test within a run:
```bash
assertllm inspect --config examples/sample1.yaml --test "cricket agent - idk question"
assertllm inspect --run runs/sample1_20250604_103500.json --test "cricket agent - idk question"
```

Argument rules for `inspect`:

- `--list` and `--run` cannot be used together. `--list` shows available runs; `--run` inspects a specific one.
- `--list` and `--test` cannot be used together. Use `--run` or `--config` with `--test` to inspect a specific run.
- `--run` and `--config` cannot be used together. `--run` is a direct path to a file; `--config` is a hint to find the latest run for that config. Pick one.
- `--test` requires either `--run` or `--config`. Without one of them it is ambiguous which run to filter from.

Exit code is 0 on all pass, 1 on any failure. Plugs into GitHub Actions with no extra config.

---

## Output

```
PASS refund policy -- 3/3 passed
FAIL summarizer -- 1/3 passed
     -> does not add facts not present in the input

2 passed, 1 failed
```

---

## Runs

Every `assertllm run` saves a structured JSON record under `runs/` in the current working directory:

```
runs/
  sample1_20250604_103500.json
  sample1_20250604_110200.json
```

Each record contains the input, raw endpoint response, assertion results, duration, and error state for every test. The `runs/` folder is gitignored by default.

Use `assertllm inspect` to browse run output without opening the JSON files directly.

---

## Judge design

One LLM call per test, not per assertion. All assertions are evaluated together in a single prompt:

```
Here is an API response:
<response>
{raw_response}
</response>

Evaluate each assertion below. Answer YES or NO for each, in the same order.

1. mentions a 30-day return window
2. does not mention a phone number
3. tone is polite

Reply in this exact format:
1. YES
2. NO
3. YES
```

The raw response from the endpoint is passed to the judge as-is. The judge LLM finds the relevant content inside any JSON shape without explicit parsing logic.

---

## Local mock server

A FastAPI mock server is included for testing without a real endpoint. It calls Groq under the hood with real system prompts, so you need `GROQ_API_KEY` set in your `.env`.

```bash
pip install fastapi uvicorn python-dotenv
uvicorn examples.mock_server.main:app --port 8000 --reload
```

Endpoints:

- `POST /chat` -- an angry cricket assistant. Answers cricket questions with attitude, refuses everything else rudely, apologises politely when it doesn't know a cricket answer.
- `POST /summarize` -- a one-sentence summarizer. Condenses the input `text` field without adding facts.
- `POST /error` -- always returns 500.

Then run against it:
```bash
assertllm run examples/sample1.yaml
```

---

## Snapshots

Snapshots are saved under `snapshots/` in the current working directory, named after the config file and timestamp:

```
snapshots/
  sample1_20250529_143022.json
  sample1_20250530_091500.json
```

`assertllm diff` auto-picks the latest snapshot for the given config. The `snapshots/` folder is gitignored by default.

---

## Dependencies

- `pydantic` -- models and validation
- `pydantic-settings` -- .env loading
- `pyyaml` -- config parsing
- `httpx` -- HTTP calls
- `groq` -- Groq judge
- `anthropic` -- Anthropic judge
- `openai` -- OpenAI judge
- `typer` -- CLI
- `rich` -- terminal output formatting