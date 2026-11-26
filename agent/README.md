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
