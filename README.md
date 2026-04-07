# Code Review Agent — OpenEnv Environment

## Submission Checklist
- [x] inference.py follows the OpenEnv template exactly
- [x] API_BASE_URL and MODEL_NAME have defaults; HF_TOKEN does not
- [x] All LLM calls use OpenAI client configured via env variables
- [x] Stdout logs follow START/STEP/END format exactly
- [x] Environment runs locally via `python inference.py`

## Overview
This project provides a reinforcement learning environment where the agent acts as an automated Python code reviewer. In each episode, the agent receives a flawed function and must classify the flaw type, explain the issue in plain language, and submit a corrected implementation. The environment then evaluates the fix by executing code against hidden-style test cases, not just text matching.

The environment is designed for GRPO-style policy optimization with TRL and OpenEnv. It produces shaped rewards that combine correctness, reasoning quality, and interaction efficiency, making it useful for training LLMs to perform practical code review tasks that require both analysis and executable fixes.

## Task Description
At reset, the agent sees:
- Problem metadata (`id`, `difficulty`, `flaw_type`)
- Natural language description of intended behavior
- Flawed Python code

At each step, the agent must submit:
- A flaw type guess (`bug`, `inefficiency`, `security`, `style`)
- A written explanation of the flaw
- A corrected version of the function (`solution`)

The grader executes the submitted code on test cases and returns structured feedback plus a composite grade.

## Observation Space

| field name | type | description |
|---|---|---|
| episode_id | str | Unique UUID for the active episode |
| step | int | Current step count |
| max_steps | int | Max allowed attempts in the episode |
| problem_id | str | Problem identifier |
| difficulty | `"easy" \| "medium" \| "hard"` | Problem difficulty level |
| flaw_type | `"bug" \| "inefficiency" \| "security" \| "style"` | Ground-truth flaw category |
| description | str | Expected function behavior |
| flawed_code | str | Python code to review |
| hint_available | bool | Whether hint was used and now visible |
| hint | str \| null | Hint text after hint request |
| cumulative_reward | float | Sum of rewards so far |
| done | bool | Episode completion flag |
| feedback | str \| null | Human-readable grader feedback |

## Action Space

| field name | type | description |
|---|---|---|
| flaw_type_guess | `"bug" \| "inefficiency" \| "security" \| "style"` | Agent guess for flaw class |
| explanation | str | Natural language explanation of flaw |
| fixed_code | str | Corrected Python implementation |
| request_hint | bool | If true, consumes one hint and triggers penalty |

## Reward Structure

| component | weight/range | condition |
|---|---|---|
| Code correctness | 0.50 (mapped to `[-0.5, +0.5]`) | Based on pass rate and runtime validity |
| Flaw type identification | 0.20 (`[0.0, +0.2]`) | +0.2 when guess is correct |
| Explanation quality | 0.20 (`[0.0, +0.2]`) | Thresholded by keyword overlap score |
| Speed bonus | 0.10 (`[0.0, +0.1]`) | +0.1 on step 1, +0.05 on step 2 |
| Hint penalty | flat `-0.20` | Applied when hint is used |

Final reward is clamped to `[-1.0, 1.0]`.

## Problem Dataset

| id | difficulty | flaw_type |
|---|---|---|
| off_by_one_loop | easy | bug |
| wrong_operator | easy | bug |
| missing_return | easy | bug |
| mutable_default_arg | medium | bug |
| integer_division | easy | bug |
| reversed_condition | easy | bug |
| infinite_loop_risk | medium | bug |
| nested_loop_search | medium | inefficiency |
| repeated_computation | easy | inefficiency |
| string_concatenation | medium | inefficiency |
| redundant_sort | easy | inefficiency |
| unnecessary_list_copy | easy | inefficiency |
| sql_injection | hard | security |
| hardcoded_secret | medium | security |
| eval_usage | hard | security |
| path_traversal | hard | security |
| god_function | hard | style |
| magic_numbers | medium | style |
| poor_naming | medium | style |
| no_error_handling | medium | style |

## Episode Lifecycle
1. Client calls `POST /reset` (or WebSocket `{"action":"reset"}`), optionally with `problem_id`.
2. Environment selects a problem, resets counters, returns initial observation (`step=0`, `done=false`).
3. Client sends `Action` payload to `POST /step` (or WebSocket `{"action":"step","payload":...}`).
4. Grader evaluates flaw type, explanation, and fixed code execution across all tests.
5. Reward module computes shaped reward breakdown.
6. Environment updates state (`step += 1`, `cumulative_reward += reward`).
7. Episode ends when all tests pass or max steps are reached.
8. Client reads `GET /state` for full trace; terminal result available via env `result()`.

Example step progression:
- Step 1: pass_rate 0.33, correct type, short explanation -> small positive reward
- Step 2: pass_rate 1.00, strong explanation -> large reward, episode done

## Grader
The grader is deterministic and programmatic:
- `execute_code()` sanitizes forbidden imports (`os`, `sys`, `subprocess`), executes submitted code, runs `solution(**kwargs)`, catches all exceptions, and enforces a 2-second timeout.
- `grade_flaw_type()` checks exact class match.
- `grade_explanation()` uses minimum length and Jaccard similarity over content tokens.
- `grade_fixed_code()` executes all test cases and computes pass rate plus execution metrics.
- `grade()` composes all sub-scores and emits feedback used by the environment.

Run built-in grading smoke tests:
```bash
python grader.py
```

## Quick Start — Local
```bash
git clone <your-repo-url>
cd code-review-env
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

Then open:
- `http://localhost:7860/health`
- `http://localhost:7860/docs`

## Running inference.py locally
```bash
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="your_hf_token_here"
python inference.py
```

## Deployment — Hugging Face Spaces
```bash
pip install openenv-core
openenv login
openenv push
```

This repository includes a Dockerfile compatible with Spaces using port `7860`.

## Example Agent Interaction
Reset:
```json
POST /reset
{
  "problem_id": "wrong_operator"
}
```

Response (`Observation`):
```json
{
  "episode_id": "a5f0c793-2a17-4d96-b58f-f7e3a3bdf855",
  "step": 0,
  "max_steps": 3,
  "problem_id": "wrong_operator",
  "difficulty": "easy",
  "flaw_type": "bug",
  "description": "Return the sum of all numbers in the list.",
  "flawed_code": "def solution(nums): ...",
  "hint_available": false,
  "hint": null,
  "cumulative_reward": 0.0,
  "done": false,
  "feedback": null
}
```

Step:
```json
POST /step
{
  "flaw_type_guess": "bug",
  "explanation": "The loop updates the accumulator using subtraction instead of addition, so the total moves in the wrong direction and returns a negative sum for positive inputs.",
  "fixed_code": "def solution(nums):\n    total = 0\n    for n in nums:\n        total += n\n    return total",
  "request_hint": false
}
```

Response (`step_result`):
```json
{
  "observation": {
    "episode_id": "a5f0c793-2a17-4d96-b58f-f7e3a3bdf855",
    "step": 1,
    "max_steps": 3,
    "problem_id": "wrong_operator",
    "difficulty": "easy",
    "flaw_type": "bug",
    "description": "Return the sum of all numbers in the list.",
    "flawed_code": "def solution(nums): ...",
    "hint_available": false,
    "hint": null,
    "cumulative_reward": 1.0,
    "done": true,
    "feedback": "Flaw type correct. Explanation score=0.75. Code pass rate=1.00 (3/3)."
  },
  "reward": 1.0,
  "done": true,
  "info": {
    "grade": {},
    "reward_breakdown": {}
  }
}
```
