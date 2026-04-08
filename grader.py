import re
import threading
import time
from typing import Any

from data.problems import PROBLEMS
from models import Action


FORBIDDEN_IMPORT_PATTERNS = [
    r"^\s*import\s+os(\s|$)",
    r"^\s*import\s+sys(\s|$)",
    r"^\s*import\s+subprocess(\s|$)",
    r"^\s*from\s+os\s+import\s+",
    r"^\s*from\s+sys\s+import\s+",
    r"^\s*from\s+subprocess\s+import\s+",
]


def _sanitize_code(code: str) -> str:
    cleaned_lines = []
    for line in code.splitlines():
        if any(re.search(pattern, line) for pattern in FORBIDDEN_IMPORT_PATTERNS):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def execute_code(code: str, test_case: dict) -> dict:
    start = time.perf_counter()
    expected_output = test_case.get("expected_output")
    result: dict[str, Any] = {
        "passed": False,
        "actual_output": None,
        "expected_output": expected_output,
        "error": None,
        "execution_time_ms": 0.0,
    }

    sanitized_code = _sanitize_code(code)
    done_flag = {"completed": False}

    def _mark_timeout() -> None:
        if not done_flag["completed"]:
            result["error"] = "TimeoutError: execution exceeded 2 seconds"

    timer = threading.Timer(2.0, _mark_timeout)

    def _runner() -> None:
        safe_builtins = {
            "abs": abs,
            "all": all,
            "any": any,
            "AttributeError": AttributeError,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "Exception": Exception,
            "float": float,
            "int": int,
            "isinstance": isinstance,
            "len": len,
            "list": list,
            "max": max,
            "min": min,
            "RuntimeError": RuntimeError,
            "range": range,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "TypeError": TypeError,
            "ValueError": ValueError,
            "__import__": __import__,
        }
        exec_ns: dict[str, Any] = {"__builtins__": safe_builtins}

        try:
            exec(sanitized_code, exec_ns, exec_ns)
            if "solution" not in exec_ns or not callable(exec_ns["solution"]):
                raise RuntimeError("No callable `solution` function found")
            actual = exec_ns["solution"](**test_case.get("input", {}))
            result["actual_output"] = actual
        except Exception as exc:  # noqa: BLE001
            result["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            done_flag["completed"] = True

    thread = threading.Thread(target=_runner, daemon=True)
    timer.start()
    thread.start()
    thread.join(2.0)
    timer.cancel()

    if thread.is_alive() and result["error"] is None:
        result["error"] = "TimeoutError: execution exceeded 2 seconds"

    if result["error"] is None:
        result["passed"] = result["actual_output"] == expected_output
    else:
        if isinstance(expected_output, str) and expected_output in result["error"]:
            result["passed"] = True
            result["actual_output"] = expected_output

    elapsed = (time.perf_counter() - start) * 1000
    result["execution_time_ms"] = round(elapsed, 4)
    return result


def grade_flaw_type(guess: str, actual: str) -> dict:
    correct = guess == actual
    return {"correct": correct, "score": 0.99 if correct else 0.01}


def _tokenize(text: str) -> set[str]:
    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "to",
        "with",
    }
    tokens = re.findall(r"[a-zA-Z_]{3,}", text.lower())
    return {tok for tok in tokens if tok not in stop_words}


def grade_explanation(explanation: str, flaw_explanation: str) -> dict:
    word_count = len(re.findall(r"\w+", explanation))
    too_short = word_count <= 20
    if too_short:
        return {"score": 0.01, "word_overlap": 0.0, "too_short": True}

    exp_tokens = _tokenize(explanation)
    gt_tokens = _tokenize(flaw_explanation)
    if not exp_tokens and not gt_tokens:
        overlap = 1.0
    elif not exp_tokens or not gt_tokens:
        overlap = 0.0
    else:
        overlap = len(exp_tokens & gt_tokens) / len(exp_tokens | gt_tokens)

    score = round(overlap, 4)
    score = max(0.01, min(0.99, score))
    return {"score": score, "word_overlap": round(overlap, 4), "too_short": False}


def grade_fixed_code(fixed_code: str, problem: dict) -> dict:
    test_results = [execute_code(fixed_code, case) for case in problem["test_cases"]]
    tests_total = len(test_results)
    tests_passed = sum(1 for r in test_results if r["passed"])
    pass_rate = tests_passed / tests_total if tests_total else 0.0
    # Clamp to strictly open interval (0, 1) as required by validator
    pass_rate = max(0.01, min(0.99, pass_rate))
    avg_execution_time_ms = (
        sum(r["execution_time_ms"] for r in test_results) / tests_total if tests_total else 0.0
    )
    return {
        "tests_passed": tests_passed,
        "tests_total": tests_total,
        "pass_rate": round(pass_rate, 4),
        "all_passed": tests_passed == tests_total,
        "test_results": test_results,
        "avg_execution_time_ms": round(avg_execution_time_ms, 4),
    }


def grade(action: Action, problem: dict) -> dict:
    flaw_type_result = grade_flaw_type(action.flaw_type_guess, problem["flaw_type"])
    explanation_result = grade_explanation(action.explanation, problem["flaw_explanation"])
    code_result = grade_fixed_code(action.fixed_code, problem)
    hint_penalty = -0.2 if action.request_hint else 0.0

    composite_score = (
        (code_result["pass_rate"] * 0.5)
        + (flaw_type_result["score"] * 0.2)
        + (explanation_result["score"] * 0.2)
        + hint_penalty
    )
    composite_score = max(-1.0, min(1.0, round(composite_score, 4)))

    feedback = (
        f"Flaw type {'correct' if flaw_type_result['correct'] else 'incorrect'}. "
        f"Explanation score={explanation_result['score']:.2f}. "
        f"Code pass rate={code_result['pass_rate']:.2f} ({code_result['tests_passed']}/{code_result['tests_total']})."
    )

    return {
        "flaw_type": flaw_type_result,
        "explanation": explanation_result,
        "code": code_result,
        "hint_penalty": hint_penalty,
        "composite_score": composite_score,
        "feedback": feedback,
    }
