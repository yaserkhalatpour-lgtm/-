"""Private task-planning API for the Khalatpour Math website.

This first milestone plans tasks only. It deliberately cannot write to GitHub,
publish pages, send messages, or delete data.
"""
from __future__ import annotations

import os
import secrets
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(
    title="Khalatpour Math AI Agent",
    version="0.1.1",
    description="Private planning service; execution tools are not enabled yet.",
)


class TaskRequest(BaseModel):
    task: str = Field(min_length=5, max_length=4000)


class TaskPlan(BaseModel):
    task: str
    plan: str
    mode: str = "planning_only"


def require_admin(authorization: Annotated[str | None, Header()] = None) -> None:
    expected = os.getenv("AGENT_ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Admin token is not configured")
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "khalatpour-math-agent", "version": "0.1.1"}


@app.post("/plan", response_model=TaskPlan, dependencies=[Depends(require_admin)])
def plan_task(request: TaskRequest) -> TaskPlan:
    api_key = os.getenv("GROQ_API_KEY", "")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    if not api_key:
        raise HTTPException(status_code=503, detail="Groq API key is not configured")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the planning component of the Khalatpour Math educational website. "
                        "Respond in Persian. Break the requested task into clear, verifiable steps. "
                        "Identify required inputs, files likely involved, risks, and acceptance tests. "
                        "Do not claim to have performed actions. This service is planning-only."
                    ),
                },
                {"role": "user", "content": request.task},
            ],
            temperature=0.2,
        )
        plan = response.choices[0].message.content or ""
    except Exception as exc:
        # Do not expose provider details or credentials to callers.
        raise HTTPException(status_code=502, detail="AI provider request failed") from exc

    return TaskPlan(task=request.task, plan=plan)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
