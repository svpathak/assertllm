# assertllm
<<<<<<< HEAD

A CLI tool that fires inputs at an AI endpoint and evaluates outputs using plain-English behavioral assertions, judged by a second LLM.

The target user is an engineer who wired up an AI endpoint and needs a smoke test that runs in CI. No platform to learn. Just a YAML file and an exit code. That's it!

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
```

Only the key for your chosen judge provider is required. API keys are never declared in the config file -- they are read from `.env` based on the provider.

assertllm reads `.env` from the directory you run it from. Keep your config and `.env` at your project root and run assertllm from there.

---

## Config

Create an `my_assertions.yaml` in your project:

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

Supported judge providers: `groq`, `anthropic`, `openai`.

By default assertllm expects a 2xx response. To test that your endpoint correctly returns an error status, declare `expected_status`:

```yaml
  - name: bad auth returns 401
    endpoint: https://your-api.com/chat
    method: POST
    headers:
      Authorization: Bearer invalid-token
    body:
      message: "hello"
    expected_status: 401
    assert:
      - response indicates unauthorized or invalid token
```

If the endpoint returns a status that does not match `expected_status`, the test is recorded as a failure. If it matches, the response body is passed to the judge as normal.

---

## Running tests

```bash
assertllm run my_assertions.yaml
```

Run a single test by name:

```bash
assertllm run my_assertions.yaml --test "refund policy"
```

Output:

```
PASS refund policy -- 3/3 passed
FAIL summarizer -- 1/3 passed
     -> does not add facts not present in the input

2 passed, 1 failed

Run #5 saved. Inspect with: assertllm inspect --config my_assertions.yaml --run 5
```

Exit code is 0 on all pass, 1 on any failure. Plugs into GitHub Actions with no extra config.

Every run is saved automatically -- there is nothing to set up or clean up. Runs are numbered sequentially per config, starting at 1.

---

## Inspecting runs

`--config` is required for `inspect` and `diff` so assertllm knows which run history to look at.

List all runs for a config, latest first, with a pass/fail/error summary:

```bash
assertllm inspect --config my_assertions.yaml --list
```

```
#5  2026-06-14T17:23:01  4 tests -- 3 passed, 1 failed
#4  2026-06-14T17:15:50  4 tests -- 4 passed
#3  2026-06-14T17:14:41  4 tests -- 2 passed, 1 failed, 1 error
```

Inspect the latest run:

```bash
assertllm inspect --config my_assertions.yaml
```

Inspect a specific run by number, or by negative index counting back from the latest (`-1` is latest, `-2` is the run before that):

```bash
assertllm inspect --config my_assertions.yaml --run 3
assertllm inspect --config my_assertions.yaml --run -2
```

Filter to a single test within a run:

```bash
assertllm inspect --config my_assertions.yaml --run 3 --test "refund policy"
```

Argument rules:

- `--list` cannot be combined with `--run` or `--test`.
- `--run` defaults to `-1` (the latest run) if not given.

---

## Comparing runs

`assertllm diff` compares two runs of the same config and flags assertions that flipped from pass to fail or fail to pass, plus tests that were added or removed between runs.

```bash
assertllm diff --config my_assertions.yaml
```

By default this compares the latest run (`head`, `-1`) against the run before it (`base`, `-2`):

```
Base: #4  2026-06-14T17:15:50
Head: #5  2026-06-14T17:23:01

OK    refund policy
DRIFT summarizer
      -> does not add facts not present in the input  (PASS -> FAIL)
OK    cricket question
```

Pin a specific baseline, comparing it against the latest run:

```bash
assertllm diff --config my_assertions.yaml --base 2
```

Compare two specific runs:

```bash
assertllm diff --config my_assertions.yaml --base 2 --head 4
```

`--head` cannot be used without `--base`. Exit code is 1 if any test drifted, 0 otherwise.

---

## Where data lives

Everything assertllm writes is kept under `.assertllm/` in your project root:

```
.assertllm/
  .runs/
    my_assertions-a1b2c3d4/
      1.json
      2.json
      ...
```

Each config gets its own folder, named from the config file and a short hash to avoid collisions. Each run is a numbered JSON file containing the input, raw endpoint response, HTTP status code, assertion results, duration, and error state for every test.

`.assertllm/` is managed entirely by the CLI. Use `assertllm inspect` to view runs -- there is no need to open these files directly.

assertllm writes its own `.gitignore` inside `.assertllm/` automatically, so its contents are never tracked even if you forget. As a safety net, it is still worth adding `.assertllm/` and `.env` explicitly to your project's `.gitignore`:

```
.assertllm/
.env
```

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

## Running the test suite

```bash
pip install -e ".[dev]"
pytest
```

Tests mock all external calls (HTTP, judge SDKs) -- no API keys or running servers required.

---

## Development

A mock server is included under `examples/mock_server/` for testing assertllm locally without a real endpoint. It is not part of the assertllm package -- it requires `fastapi`, `uvicorn`, `python-dotenv`, and its own `.env` with `GROQ_API_KEY`.

```bash
uvicorn examples.mock_server.main:app --port 8000 --reload
assertllm run examples/configs/sample1.yaml
```
=======
A CLI tool that fires inputs at an AI endpoint and evaluates outputs using plain-English behavioral assertions.
>>>>>>> origin/main
