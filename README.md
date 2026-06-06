# assertllm

A CLI tool that fires inputs at an AI endpoint and evaluates outputs using plain-English behavioral assertions, judged by a second LLM.

The target user is an engineer who wired up an AI endpoint and needs a smoke test that runs in CI. No platform to learn. Just a YAML file and an exit code.

---

## How it works

```
Write a YAML config
        ↓
CLI reads and validates it
        ↓
For each test:
    → Fire input at endpoint
    → Get raw response
    → Send response + assertions to judge LLM
    → Get pass/fail per assertion
        ↓
Print summary to terminal
        ↓
Exit 0 (all pass) or 1 (any failure)
```

---

## Install

```bash
git clone https://github.com/svpathak/assertllm.git
cd assertllm
pip install -e .
```

---

## Setup

Create a `.env` file in your project root with keys for your chosen judge provider:

```
GROQ_API_KEY=your-groq-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
OLLAMA_HOST=http://localhost:11434
```

Only the key for your chosen judge provider is required. API keys are never declared in the config file -- they are read from `.env` based on the provider.

assertllm reads `.env` from the directory you run it from. Keep your config and `.env` at your project root and run assertllm from there.

---

## Config

Create an `assertllm.yaml` in your project:

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

Supported judge providers: `groq`, `anthropic`, `openai`, `ollama`.

---

## Commands

Run all tests:
```bash
assertllm run assertllm.yaml
```

Run a single test by name:
```bash
assertllm run assertllm.yaml --test "refund policy"
```

Save a snapshot of current endpoint responses:
```bash
assertllm snapshot assertllm.yaml
```

Compare current responses against the latest snapshot:
```bash
assertllm diff assertllm.yaml
```

Compare against a specific snapshot:
```bash
assertllm diff assertllm.yaml --snapshot snapshots/assertllm_20250529_143022.json
```

List all saved runs:
```bash
assertllm inspect --list
```

List runs for a specific config:
```bash
assertllm inspect --list --config assertllm.yaml
```

Inspect the latest run:
```bash
assertllm inspect
```

Inspect the latest run for a specific config:
```bash
assertllm inspect --config assertllm.yaml
```

Inspect a specific run file:
```bash
assertllm inspect --run runs/assertllm_20250604_103500.json
```

Filter to a single test within a run:
```bash
assertllm inspect --config assertllm.yaml --test "refund policy"
assertllm inspect --run runs/assertllm_20250604_103500.json --test "refund policy"
```

Argument rules for `inspect`:

- `--list` and `--run` cannot be used together. `--list` shows available runs; `--run` inspects a specific one.
- `--list` and `--test` cannot be used together. Use `--run` or `--config` with `--test` to inspect a specific run.
- `--run` and `--config` cannot be used together. `--run` is a direct path; `--config` finds the latest run for that config.
- `--test` requires either `--run` or `--config`.

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

Every `assertllm run` saves a structured JSON record under `runs/` in your project directory:

```
runs/
  assertllm_20250604_103500.json
  assertllm_20250604_110200.json
```

Each record contains the input, raw endpoint response, assertion results, duration, and error state for every test. Use `assertllm inspect` to browse runs without opening the JSON files directly.

---

## Snapshots

Snapshots are saved under `snapshots/` in your project directory:

```
snapshots/
  assertllm_20250529_143022.json
  assertllm_20250530_091500.json
```

`assertllm diff` auto-picks the latest snapshot for the given config.

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

---

## Development

The repo includes a mock server for testing assertllm locally without a real endpoint. It is not part of the assertllm package.

```bash
pip install fastapi uvicorn python-dotenv
```

Add `GROQ_API_KEY` to a `.env` inside `examples/mock_server/`, then start the server:

```bash
uvicorn examples.mock_server.main:app --port 8000 --reload
```

Endpoints:

- `POST /chat` -- an angry cricket assistant powered by Groq. Answers cricket questions with attitude, refuses everything else rudely, apologises politely when it doesn't know a cricket answer.
- `POST /summarize` -- a one-sentence summarizer powered by Groq. Condenses the input `text` field without adding facts.
- `POST /error` -- always returns 500.

Run the included sample config against it:

```bash
assertllm run examples/sample1.yaml
```