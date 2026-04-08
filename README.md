---
title: Code Review Env
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# Code Review Agent — OpenEnv Environment

> A reinforcement learning environment where an AI agent learns to review 
> Python code like a senior engineer. Built for the Meta × PyTorch × 
> Hugging Face OpenEnv Hackathon.

## Why This Environment?

Code review is one of the highest-value real-world tasks for LLM agents:
- Every software team does it daily
- It requires multi-step reasoning: read → diagnose → fix → verify
- It has clear, programmatic success criteria (does the fixed code pass tests?)
- It spans multiple difficulty levels naturally (bugs → inefficiencies → security)

This environment trains agents to be better code reviewers through 
reinforcement learning, rewarding correctness, explanation quality, and efficiency.

## Task Description

Each episode:
1. Agent receives a flawed Python function + description of what it should do
2. Agent must identify the flaw type (bug / inefficiency / security / style)
3. Agent must explain the flaw in plain English
4. Agent must submit a corrected version of the function
5. Grader executes the fixed code against hidden test cases and returns reward

## Observation Space

| Field | Type | Description |
|---|---|---|
| episode_id | str | Unique episode identifier |
| step | int | Current step number |
| max_steps | int | Maximum steps per episode (default: 3) |
| problem_id | str | Identifier of the current problem |
| difficulty | easy/medium/hard | Problem difficulty level |
| flaw_type | bug/inefficiency/security/style | Category of flaw |
| description | str | What the function is supposed to do |
| flawed_code | str | The broken/bad Python function to review |
| hint_available | bool | Whether a hint is available (costs -0.20 reward) |
| hint | str or null | Populated only after agent requests hint |
| cumulative_reward | float | Running reward total |
| done | bool | Whether episode is complete |
| feedback | str or null | Grader feedback after each step |

## Action Space

| Field | Type | Description |
|---|---|---|
| flaw_type_guess | bug/inefficiency/security/style | Agent's flaw classification |
| explanation | str | Plain English explanation of the flaw (>20 words for credit) |
| fixed_code | str | Complete corrected Python function |
| request_hint | bool | Set True to receive hint (-0.20 reward penalty) |

## Reward Structure

| Component | Weight | Condition | Reward |
|---|---|---|---|
| Code correctness | 0.50 | All tests pass | +0.50 |
| Code correctness | 0.50 | ≥75% tests pass | +0.35 |
| Code correctness | 0.50 | ≥50% tests pass | +0.20 |
| Code correctness | 0.50 | ≥25% tests pass | +0.08 |
| Code correctness | 0.50 | >0% tests pass | +0.05 |
| Code correctness | 0.50 | All tests fail | -0.10 |
| Code correctness | 0.50 | SyntaxError | -0.50 |
| Flaw type ID | 0.20 | Correct classification | +0.20 |
| Explanation | 0.20 | Score ≥ 0.7 | +0.20 |
| Explanation | 0.20 | Score ≥ 0.5 | +0.14 |
| Explanation | 0.20 | Score ≥ 0.3 | +0.08 |
| Speed bonus | 0.10 | Solved on step 1 | +0.10 |
| Speed bonus | 0.10 | Solved on step 2 | +0.05 |
| Difficulty bonus | — | Hard problem, all pass | +0.05 |
| Difficulty bonus | — | Medium problem, all pass | +0.02 |
| Hint penalty | — | Hint requested | -0.20 |
| **Final reward** | | **Clamped to (0.01, 0.99)** | |

## Problem Dataset (20 Problems)

| ID | Difficulty | Flaw Type | Task Group |
|---|---|---|---|
| off_by_one_loop | easy | bug | easy_bug_fix |
| wrong_operator | easy | bug | easy_bug_fix |
| missing_return | easy | bug | easy_bug_fix |
| mutable_default_arg | easy | bug | easy_mutable_default |
| integer_division | easy | bug | easy_mutable_default |
| reversed_condition | easy | bug | easy_mutable_default |
| infinite_loop_risk | easy | bug | easy_loop_bug |
| nested_loop_search | medium | inefficiency | medium_inefficiency_lookup |
| repeated_computation | medium | inefficiency | medium_inefficiency_lookup |
| string_concatenation | medium | inefficiency | medium_inefficiency_string |
| redundant_sort | medium | inefficiency | medium_inefficiency_string |
| unnecessary_list_copy | medium | inefficiency | medium_inefficiency_string |
| sql_injection | hard | security | hard_security_injection |
| hardcoded_secret | hard | security | hard_security_injection |
| eval_usage | hard | security | hard_security_execution |
| path_traversal | hard | security | hard_security_execution |
| god_function | hard | style | hard_style_decomposition |
| magic_numbers | hard | style | hard_style_decomposition |
| poor_naming | hard | style | hard_style_decomposition |
| no_error_handling | hard | style | hard_style_decomposition |

## Baseline Scores (Llama-3.1-8B-Instruct)

| Task | Difficulty | Avg Reward | Pass Rate |
|---|---|---|---|
| easy_bug_fix | easy | ~0.65 | ~78% |
| easy_mutable_default | easy | ~0.58 | ~70% |
| easy_loop_bug | easy | ~0.55 | ~65% |
| medium_inefficiency_lookup | medium | ~0.42 | ~50% |
| medium_inefficiency_string | medium | ~0.38 | ~45% |
| hard_security_injection | hard | ~0.28 | ~30% |
| hard_security_execution | hard | ~0.25 | ~28% |
| hard_style_decomposition | hard | ~0.18 | ~20% |

## Episode Lifecycle
env.reset()
→ Observation(flawed_code, description, flaw_type, difficulty)
agent reads observation
→ builds Action(flaw_type_guess, explanation, fixed_code)
env.step(action)
→ grader executes fixed_code against test cases
→ reward computed across 4 dimensions
→ Observation(feedback) returned
repeat up to max_steps=3 times
→ done=True when all tests pass OR max_steps reached
env.result() → EpisodeResult(total_reward, passed_all_tests, steps_taken)

## Grader

The grader dynamically `exec()`s the agent's fixed code in a sandboxed 
namespace, calls the function with test case kwargs, and compares output 
to expected values. Key safety features:
- 2-second timeout per test case using `threading.Timer`
- `os`, `sys`, `subprocess` imports stripped from exec namespace
- All exceptions caught and reported (SyntaxError, RuntimeError, TypeError)

## Quick Start

```bash
git clone https://github.com/Adithkp03/code-review-env
cd code-review-env
pip install -r requirements.txt
uvicorn app:app --port 7860
# Then visit http://localhost:7860/health
```

## Running the Baseline

```bash
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="your_hf_token_here"
python inference.py
```

## Deployment — Hugging Face Spaces

```bash
git remote add space https://huggingface.co/spaces/Adithkp03/code-review-env
git push space main
```

## Example API Interaction

```bash
# Reset
curl -X POST https://Adithkp03-code-review-env.hf.space/reset \
  -H "Content-Type: application/json" -d '{}'

# Step
curl -X POST https://Adithkp03-code-review-env.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "flaw_type_guess": "bug",
    "explanation": "The loop uses range(len(lst)-1) which misses the last element. It should use range(len(lst)).",
    "fixed_code": "def sum_list(lst):\n    total = 0\n    for i in range(len(lst)):\n        total += lst[i]\n    return total",
    "request_hint": false
  }'

# Health check
curl https://Adithkp03-code-review-env.hf.space/health

# List all tasks
curl https://Adithkp03-code-review-env.hf.space/tasks
```
