import sys

import grader
from data.problems import PROBLEMS
from models import Action


def run() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    perfect_explanation = (
        "The function includes a clear flaw affecting correctness, safety, or quality. "
        "The issue is explained by identifying the exact problematic logic and why it fails "
        "under expected inputs, and the correction restores intended behavior cleanly."
    )
    wrong_explanation = "This is bad."

    print("ID                    | Difficulty | Flaw Type    | Perfect ✓/✗ | Wrong ✓/✗")
    print("----------------------|------------|--------------|-------------|----------")

    all_perfect_passed = True
    for problem in PROBLEMS:
        perfect_action = Action(
            flaw_type_guess=problem["flaw_type"],
            explanation=perfect_explanation,
            fixed_code=problem["correct_code"],
            request_hint=False,
        )
        wrong_action = Action(
            flaw_type_guess="style",
            explanation=wrong_explanation,
            fixed_code=problem["flawed_code"],
            request_hint=False,
        )

        perfect_grade = grader.grade(perfect_action, problem)
        wrong_grade = grader.grade(wrong_action, problem)
        perfect_pass = perfect_grade["code"]["all_passed"]
        wrong_pass = wrong_grade["code"]["all_passed"]
        all_perfect_passed = all_perfect_passed and perfect_pass

        perfect_text = "✓ PASS" if perfect_pass else "✗ FAIL"
        wrong_text = "✓ PASS" if wrong_pass else "✗ FAIL"
        print(
            f"{problem['id'][:22]:22} | "
            f"{problem['difficulty']:<10} | "
            f"{problem['flaw_type']:<12} | "
            f"{perfect_text:<11} | "
            f"{wrong_text:<8}"
        )

    return 0 if all_perfect_passed else 1


if __name__ == "__main__":
    raise SystemExit(run())
