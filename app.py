from typing import Any, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from data.problems import PROBLEMS
from envs.code_review_env import CodeReviewEnv
from models import Action

app = FastAPI(title="Code Review Agent OpenEnv")

active_envs: dict[str, CodeReviewEnv] = {}
DEFAULT_HTTP_SESSION = "http_default"


class ResetRequest(BaseModel):
    problem_id: Optional[str] = None


def _get_or_create_env(session_id: str) -> CodeReviewEnv:
    if session_id not in active_envs:
        active_envs[session_id] = CodeReviewEnv()
    return active_envs[session_id]


@app.post("/reset")
async def reset(body: ResetRequest = None) -> dict[str, Any]:
    problem_id = body.problem_id if body else None
    env = _get_or_create_env(DEFAULT_HTTP_SESSION)
    try:
        observation = env.reset(problem_id=problem_id)
        return observation.model_dump()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "Code Review Agent"}


@app.post("/step")
def step(action: Action) -> dict[str, Any]:
    env = _get_or_create_env(DEFAULT_HTTP_SESSION)
    try:
        observation, reward, done, info = env.step(action)
        return {
            "observation": observation.model_dump(),
            "reward": reward,
            "done": done,
            "info": info,
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/state")
def state() -> dict[str, Any]:
    env = _get_or_create_env(DEFAULT_HTTP_SESSION)
    try:
        return env.state().model_dump()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/problems")
def problems() -> list[dict[str, str]]:
    return [
        {
            "id": problem["id"],
            "difficulty": problem["difficulty"],
            "flaw_type": problem["flaw_type"],
        }
        for problem in PROBLEMS
    ]


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "problems_loaded": len(PROBLEMS)}


@app.get("/tasks")
async def get_tasks():
    return {
        "tasks": [
            {"name": "bug_detection", "description": "Identify and fix bugs", "grader": "grader.py"},
            {"name": "inefficiency_detection", "description": "Identify and fix inefficiencies", "grader": "grader.py"},
            {"name": "security_review", "description": "Identify and fix security issues", "grader": "grader.py"},
            {"name": "style_improvement", "description": "Identify and fix style issues", "grader": "grader.py"},
        ],
        "total": 4
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    session_id = str(id(websocket))
    active_envs[session_id] = CodeReviewEnv()

    try:
        while True:
            message = await websocket.receive_json()
            action_type = message.get("action")
            payload = message.get("payload", {})
            env = _get_or_create_env(session_id)

            if action_type == "reset":
                observation = env.reset(problem_id=payload.get("problem_id"))
                await websocket.send_json({"type": "observation", "data": observation.model_dump()})
            elif action_type == "step":
                action = Action(**payload)
                observation, reward, done, info = env.step(action)
                await websocket.send_json(
                    {
                        "type": "step_result",
                        "data": {
                            "observation": observation.model_dump(),
                            "reward": reward,
                            "done": done,
                            "info": info,
                        },
                    }
                )
            elif action_type == "state":
                await websocket.send_json({"type": "state", "data": env.state().model_dump()})
            else:
                await websocket.send_json(
                    {"type": "error", "data": {"message": f"Unknown action: {action_type}"}}
                )
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        await websocket.send_json({"type": "error", "data": {"message": str(exc)}})
    finally:
        active_envs.pop(session_id, None)
