from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import run_agent


app = FastAPI(
    title="Sunrise Clinic Front Desk Agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Request schema — exactly matches schema.md
# ============================================================

class AgentRequest(BaseModel):
    conversation_id: str
    today: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    turns: List[str]


# ============================================================
# Evaluator endpoint
# ============================================================

@app.post("/agent/run")
def agent_run(request: AgentRequest):

    return run_agent(
        conversation_id=request.conversation_id,
        today=request.today,
        turns=request.turns,
    )


# ============================================================
# Health check
# ============================================================

@app.get("/health")
def health_check():
    return {"status": "ok"}