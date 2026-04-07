import json
import os
import re
import traceback

from openai import OpenAI

from envs.code_review_env import CodeReviewEnv
from models import Action

API_BASE_URL = os.getenv("API_BASE_URL", "https://api-inference.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

try:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
except Exception:  # noqa: BLE001
    client = None


def build_prompt(observation: dict) -> str:
    return (
        "You are a senior Python code reviewer.\n"
        "Given the flawed function and task details, return ONLY JSON matching this schema:\n"
        "{\n"
        '  "flaw_type_guess": "bug" | "inefficiency" | "security" | "style",\n'
        '  "explanation": "plain English explanation of the flaw",\n'
        '  "fixed_code": "complete corrected Python function",\n'
        '  "request_hint": false\n'
        "}\n\n"
        f"Problem ID: {observation['problem_id']}\n"
        f"Description: {observation['description']}\n"
        f"Ground Truth Flaw Type (for training context): {observation['flaw_type']}\n"
        "Flawed Code:\n"
        f"{observation['flawed_code']}\n"
    )


def extract_json_payload(text: str) -> dict | None:
    # Try fenced JSON first.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except Exception:  # noqa: BLE001
            pass

    # Fallback: first top-level object looking chunk.
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:  # noqa: BLE001
            return None
    return None


def fallback_action(observation: dict) -> Action:
    return Action(
        flaw_type_guess="bug",
        explanation="parse error",
        fixed_code=observation["flawed_code"],
        request_hint=False,
    )


def llm_to_action(observation: dict) -> Action:
    prompt = build_prompt(observation)
    if client is None:
        return fallback_action(observation)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        payload = extract_json_payload(content)
        if payload is None:
            return fallback_action(observation)

        return Action(
            flaw_type_guess=payload.get("flaw_type_guess", "bug"),
            explanation=payload.get("explanation", "parse error"),
            fixed_code=payload.get("fixed_code", observation["flawed_code"]),
            request_hint=bool(payload.get("request_hint", False)),
        )
    except Exception:  # noqa: BLE001
        return fallback_action(observation)


def run_episode() -> None:
    env = CodeReviewEnv(max_steps=3, randomize=True)
    observation = env.reset().model_dump()

    while True:
        action = llm_to_action(observation)
        next_observation, reward, done, info = env.step(action)

        grade = info.get("grade", {})
        code_grade = grade.get("code", {})
        flaw_type_grade = grade.get("flaw_type", {})
        step_data = {
            "step": next_observation.step,
            "problem_id": next_observation.problem_id,
            "action": {
                "flaw_type_guess": action.flaw_type_guess,
                "explanation": action.explanation,
                "fixed_code": action.fixed_code,
            },
            "reward": reward,
            "done": done,
            "grade_summary": {
                "tests_passed": code_grade.get("tests_passed", 0),
                "tests_total": code_grade.get("tests_total", 0),
                "flaw_type_correct": flaw_type_grade.get("correct", False),
            },
        }
        print(f"STEP: {json.dumps(step_data)}")

        if done or next_observation.step >= next_observation.max_steps:
            break
        observation = next_observation.model_dump()


if __name__ == "__main__":
    print("START")
    try:
        run_episode()
    except Exception:  # noqa: BLE001
        error_data = {
            "step": -1,
            "problem_id": "unknown",
            "action": {
                "flaw_type_guess": "bug",
                "explanation": "parse error",
                "fixed_code": "def solution(*args, **kwargs):\n    return None",
            },
            "reward": 0.0,
            "done": True,
            "grade_summary": {"tests_passed": 0, "tests_total": 0, "flaw_type_correct": False},
            "error": traceback.format_exc(limit=1),
        }
        print(f"STEP: {json.dumps(error_data)}")
    finally:
        print("END")
