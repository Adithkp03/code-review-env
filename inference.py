import json
import os
import re
import traceback

from openai import OpenAI

from envs.code_review_env import CodeReviewEnv
from models import Action

API_BASE_URL = os.getenv("API_BASE_URL", "<your-active-endpoint>")
MODEL_NAME = os.getenv("MODEL_NAME", "<your-active-model>")
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


def run_episode(task_name: str = "easy_bug_fix", problem_id: str = None) -> None:
    env = CodeReviewEnv(max_steps=3, randomize=(problem_id is None))

    if problem_id:
        observation = env.reset(problem_id=problem_id).model_dump()
    else:
        observation = env.reset().model_dump()

    print(f"[START] task={task_name}", flush=True)

    cumulative_reward = 0.0
    total_steps = 0

    while True:
        action = llm_to_action(observation)
        next_observation, reward, done, info = env.step(action)

        cumulative_reward += reward
        total_steps += 1

        grade = info.get("grade", {})
        code_grade = grade.get("code", {})
        flaw_type_grade = grade.get("flaw_type", {})

        print(
            f"[STEP] step={total_steps} "
            f"reward={reward:.4f} "
            f"done={done} "
            f"flaw_type_correct={flaw_type_grade.get('correct', False)} "
            f"tests_passed={code_grade.get('tests_passed', 0)} "
            f"tests_total={code_grade.get('tests_total', 0)}",
            flush=True
        )

        if done or next_observation.step >= next_observation.max_steps:
            break
        observation = next_observation.model_dump()

    print(f"[END] task={task_name} score={cumulative_reward:.4f} steps={total_steps}", flush=True)


TASK_PROBLEM_MAP = {
    "easy_bug_fix": "off_by_one_loop",
    "medium_security_review": "sql_injection",
    "hard_inefficiency_fix": "nested_loop_search",
}

if __name__ == "__main__":
    for task_name, problem_id in TASK_PROBLEM_MAP.items():
        try:
            run_episode(task_name=task_name, problem_id=problem_id)
        except Exception:
            print(f"[START] task={task_name}", flush=True)
            print(f"[STEP] step=-1 reward=0.0 done=True flaw_type_correct=False tests_passed=0 tests_total=0", flush=True)
            print(f"[END] task={task_name} score=0.0 steps=0", flush=True)
