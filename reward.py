def compute_reward(grade_result: dict, step_num: int, max_steps: int) -> tuple[float, dict]:
    code = grade_result["code"]
    pass_rate = code["pass_rate"]
    all_passed = code["all_passed"]

    syntax_error = any(
        isinstance(result.get("error"), str) and "SyntaxError" in result["error"]
        for result in code["test_results"]
    )

    if syntax_error:
        code_reward = -0.5
    elif all_passed:
        code_reward = 0.5
    elif pass_rate >= 0.5:
        code_reward = 0.2
    elif 0 < pass_rate < 0.5:
        code_reward = 0.05
    else:
        code_reward = -0.1

    flaw_type_reward = 0.2 if grade_result["flaw_type"]["correct"] else 0.0

    explanation = grade_result["explanation"]
    if explanation["too_short"]:
        explanation_reward = 0.0
    elif explanation["score"] >= 0.7:
        explanation_reward = 0.2
    elif explanation["score"] >= 0.4:
        explanation_reward = 0.1
    elif explanation["score"] >= 0.2:
        explanation_reward = 0.05
    else:
        explanation_reward = 0.0

    if step_num == 1:
        speed_bonus = 0.10
    elif step_num == 2:
        speed_bonus = 0.05
    else:
        speed_bonus = 0.0

    hint_penalty = -0.20 if grade_result.get("hint_penalty", 0.0) < 0 else 0.0

    total = code_reward + flaw_type_reward + explanation_reward + speed_bonus + hint_penalty
    total = max(-1.0, min(1.0, round(total, 4)))

    breakdown = {
        "total": total,
        "code_reward": round(code_reward, 4),
        "flaw_type_reward": round(flaw_type_reward, 4),
        "explanation_reward": round(explanation_reward, 4),
        "speed_bonus": round(speed_bonus, 4),
        "hint_penalty": round(hint_penalty, 4),
    }
    return total, breakdown
