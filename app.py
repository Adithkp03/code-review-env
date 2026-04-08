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
async def list_tasks():
    """List all tasks with their graders - required by OpenEnv validator."""
    return {
        "tasks": [
            {
                "id": "easy_bug_fix",
                "name": "easy_bug_fix",
                "difficulty": "easy",
                "description": "Fix a simple off-by-one or operator bug in a Python function",
                "grader": "grader.grade_fixed_code",
                "reward_range": [0.0, 1.0],
                "problem_ids": ["off_by_one_loop", "wrong_operator", "missing_return",
                                "mutable_default_arg", "integer_division",
                                "reversed_condition", "infinite_loop_risk"]
            },
            {
                "id": "medium_security_review",
                "name": "medium_security_review",
                "difficulty": "medium",
                "description": "Identify and fix a security vulnerability",
                "grader": "grader.grade_fixed_code",
                "reward_range": [0.0, 1.0],
                "problem_ids": ["sql_injection", "hardcoded_secret",
                                "eval_usage", "path_traversal"]
            },
            {
                "id": "hard_inefficiency_fix",
                "name": "hard_inefficiency_fix",
                "difficulty": "hard",
                "description": "Identify and fix a performance inefficiency",
                "grader": "grader.grade_fixed_code",
                "reward_range": [0.0, 1.0],
                "problem_ids": ["nested_loop_search", "repeated_computation",
                                "string_concatenation", "redundant_sort",
                                "unnecessary_list_copy"]
            }
        ],
        "total_tasks": 3,
        "total_problems": 20
    }


@app.post("/grade")
async def grade_task(request: dict):
    """Run grader on a task - required by OpenEnv validator."""
    from grader import grade_fixed_code
    from data.problems import PROBLEMS

    task_id = request.get("task_id", "easy_bug_fix")
    fixed_code = request.get("fixed_code", "")
    problem_id = request.get("problem_id", None)

    # Map task_id to a representative problem
    task_problem_map = {
        "easy_bug_fix": "off_by_one_loop",
        "medium_security_review": "sql_injection",
        "hard_inefficiency_fix": "nested_loop_search"
    }

    if problem_id is None:
        problem_id = task_problem_map.get(task_id, "off_by_one_loop")

    problem = next((p for p in PROBLEMS if p["id"] == problem_id), PROBLEMS[0])

    if not fixed_code:
        fixed_code = problem["correct_code"]

    result = grade_fixed_code(fixed_code, problem)
    raw_score = result["pass_rate"]
    score = max(0.01, min(0.99, raw_score))

    return {
        "task_id": task_id,
        "problem_id": problem_id,
        "score": score,
        "reward": score,
        "pass_rate": score,
        "tests_passed": result["tests_passed"],
        "tests_total": result["tests_total"],
        "reward_range": [0.01, 0.99]
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
