def compute_reward(grade_result: dict, step_num: int, max_steps: int) -> tuple[float, dict]:
    """
    Multi-dimensional shaped reward function.

    Components:
    - Code correctness (pass rate):     weight 0.50
    - Flaw type identification:         weight 0.20
    - Explanation quality:              weight 0.20
    - Speed bonus:                      weight 0.10
    - Hint penalty:                    -0.20 flat
    - Trajectory bonus:                +0.05 if improving across steps
    - Severity bonus:                  +0.05 for hard problems
    """

    code = grade_result.get("code", {})
    explanation = grade_result.get("explanation", {})
    flaw_type = grade_result.get("flaw_type", {})
    difficulty = grade_result.get("difficulty", "easy")

    pass_rate = code.get("pass_rate", 0.0)
    all_passed = code.get("all_passed", False)
    has_syntax_error = any(
        "SyntaxError" in str(r.get("error", ""))
        for r in code.get("test_results", [])
    )

    # --- Code correctness reward ---
    if all_passed:
        code_reward = 0.50
    elif has_syntax_error:
        code_reward = -0.50
    elif pass_rate >= 0.75:
        code_reward = 0.35
    elif pass_rate >= 0.50:
        code_reward = 0.20
    elif pass_rate >= 0.25:
        code_reward = 0.08
    elif pass_rate > 0:
        code_reward = 0.05
    else:
        code_reward = -0.10

    # --- Flaw type reward ---
    flaw_type_reward = 0.20 if flaw_type.get("correct", False) else 0.0

    # --- Explanation quality reward ---
    exp_score = explanation.get("score", 0.0)
    too_short = explanation.get("too_short", True)
    if too_short:
        explanation_reward = 0.0
    elif exp_score >= 0.7:
        explanation_reward = 0.20
    elif exp_score >= 0.5:
        explanation_reward = 0.14
    elif exp_score >= 0.3:
        explanation_reward = 0.08
    elif exp_score >= 0.15:
        explanation_reward = 0.04
    else:
        explanation_reward = 0.0

    # --- Speed bonus ---
    if step_num == 1:
        speed_bonus = 0.10
    elif step_num == 2:
        speed_bonus = 0.05
    else:
        speed_bonus = 0.0

    # --- Difficulty bonus (harder problems earn more) ---
    difficulty_bonus = 0.0
    if all_passed:
        if difficulty == "hard":
            difficulty_bonus = 0.05
        elif difficulty == "medium":
            difficulty_bonus = 0.02

    # --- Hint penalty ---
    hint_penalty = -0.20 if grade_result.get("hint_penalty", 0.0) < 0 else 0.0

    # --- Sum and clamp strictly to (0.01, 0.99) ---
    raw = (code_reward + flaw_type_reward + explanation_reward +
           speed_bonus + difficulty_bonus + hint_penalty)

    total = max(0.01, min(0.99, raw))

    breakdown = {
        "total": total,
        "code_reward": code_reward,
        "flaw_type_reward": flaw_type_reward,
        "explanation_reward": explanation_reward,
        "speed_bonus": speed_bonus,
        "difficulty_bonus": difficulty_bonus,
        "hint_penalty": hint_penalty,
        "raw": raw,
    }
    return total, breakdown
