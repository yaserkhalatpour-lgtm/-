# Khalatpour Math AI Agent — foundation

This is the first, deliberately limited milestone of the private AI agent for
`yaserkhalatpour-lgtm/-`.

## Current capability

- Private FastAPI service.
- Health endpoint: `GET /health`.
- Authenticated task planning endpoint: `POST /plan`.
- Uses Groq's OpenAI-compatible Chat Completions API.
- Persian plans with steps, dependencies, risks, and acceptance checks.
- Default model: `openai/gpt-oss-120b` (subject to Groq free-plan availability and limits).

## Not enabled yet

This version **does not** edit GitHub files, merge pull requests, deploy the
website, access student data, send messages, or run shell commands. It must not
be described as a fully autonomous executor until those capabilities have
been implemented and tested.

## Local setup

1. Use Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Install: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env`.
5. Set `GROQ_API_KEY`, optionally `GROQ_MODEL`, and a long random
   `AGENT_ADMIN_TOKEN` in the local environment. Never commit `.env`.
6. Run: `uvicorn app:app --host 127.0.0.1 --port 8000`.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/plan \
  -H "Authorization: Bearer $AGENT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task":"صفحه درس تابع را برای ریاضی دهم برنامه‌ریزی کن"}'
```

## Security and next milestones

- Keep this service private; do not expose it directly to the public website.
- Store secrets only in the hosting provider's secret manager.
- Next: read-only GitHub inspection, isolated branch writes, automated tests,
  pull-request creation, preview deployment, and only then bounded auto-merge.
- Destructive operations, handling private student information, public
  communications, and production credential changes require explicit approval.
- Log task IDs and outcomes, but never log API keys or authorization headers.


## Shad worker scaffold (disabled)

A separate `shad_worker.py` preflight process is included in the container.
It is intentionally fail-closed:

- `SHAD_ENABLED=false` by default.
- `SHAD_DRY_RUN=true` and `SHAD_AUTO_REPLY=false` by default.
- It does not authenticate, poll Shad, read messages, or send messages.
- It refuses live operation until a controlled test verifies that the
  library's update cursor excludes all messages sent before activation.

For a separate background-worker service, use the same Docker image and
override its start command to `python shad_worker.py`. Do not deploy it as a
live integration yet. Mount any future session directory as a private secret
volume outside the repository; never put session files in environment values
or GitHub.


## Offline safety tests

Run the Shad worker's fail-closed tests without network access:

```bash
python -m unittest discover -s agent -p 'test_*.py' -v
```

These tests verify disabled-by-default behavior, the no-network dry-run path,
missing-group refusal, rejection of live mode, and invalid boolean settings.
They do not authenticate with Shad or validate the third-party client's
message-update semantics.

## Continuous integration

GitHub Actions runs the offline Python compilation and Shad worker safety tests
on pushes and pull requests targeting `ai-agent-foundation`. These checks do
not connect to Shad and do not validate the third-party client's live update
cursor behavior.
