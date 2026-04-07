import random
import uuid

import grader
import reward
from data.problems import PROBLEMS
from models import Action, EpisodeResult, Observation, State


class CodeReviewEnv:
    def __init__(self, max_steps: int = 3, randomize: bool = True):
        self.max_steps = max_steps
        self.randomize = randomize
        self.problems = PROBLEMS
        self.problem_map = {problem["id"]: problem for problem in self.problems}

        self.episode_id = ""
        self.current_problem = None
        self.step_count = 0
        self.done = False
        self.hint_used = False
        self.cumulative_reward = 0.0
        self.grade_history: list[dict] = []

    def reset(self, problem_id: str = None) -> Observation:
        if problem_id:
            if problem_id not in self.problem_map:
                raise ValueError(f"Unknown problem_id: {problem_id}")
            problem = self.problem_map[problem_id]
        else:
            if self.randomize:
                problem = random.choice(self.problems)
            else:
                problem = self.problems[0]

        self.episode_id = str(uuid.uuid4())
        self.current_problem = problem
        self.step_count = 0
        self.done = False
        self.hint_used = False
        self.cumulative_reward = 0.0
        self.grade_history = []
        return self._build_observation(feedback=None)

    def step(self, action: Action) -> tuple[Observation, float, bool, dict]:
        if self.current_problem is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        if self.done:
            raise RuntimeError("Episode already done. Call reset() to start a new one.")

        if action.request_hint and not self.hint_used:
            self.hint_used = True

        grade_result = grader.grade(action, self.current_problem)
        if self.hint_used:
            grade_result["hint_penalty"] = -0.2

        next_step_number = self.step_count + 1
        reward_value, reward_breakdown = reward.compute_reward(
            grade_result=grade_result,
            step_num=next_step_number,
            max_steps=self.max_steps,
        )

        self.step_count = next_step_number
        solved = grade_result["code"]["all_passed"]
        self.done = solved or self.step_count >= self.max_steps
        self.cumulative_reward += reward_value
        self.grade_history.append(
            {"step": self.step_count, "grade": grade_result, "reward_breakdown": reward_breakdown}
        )

        observation = self._build_observation(feedback=grade_result["feedback"])
        info = {"grade": grade_result, "reward_breakdown": reward_breakdown}
        return observation, reward_value, self.done, info

    def state(self) -> State:
        if self.current_problem is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        return State(
            episode_id=self.episode_id,
            problem_id=self.current_problem["id"],
            step=self.step_count,
            max_steps=self.max_steps,
            hint_used=self.hint_used,
            cumulative_reward=round(self.cumulative_reward, 4),
            done=self.done,
            grade_history=self.grade_history,
        )

    def result(self) -> EpisodeResult:
        if not self.done:
            raise RuntimeError("Episode is not complete yet.")
        if not self.grade_history:
            raise RuntimeError("No grades available for this episode.")

        final_grade = self.grade_history[-1]["grade"]
        return EpisodeResult(
            episode_id=self.episode_id,
            problem_id=self.current_problem["id"],
            difficulty=self.current_problem["difficulty"],
            flaw_type=self.current_problem["flaw_type"],
            total_reward=round(self.cumulative_reward, 4),
            steps_taken=self.step_count,
            hint_used=self.hint_used,
            passed_all_tests=final_grade["code"]["all_passed"],
            final_grade=final_grade,
        )

    def _build_observation(self, feedback: str | None) -> Observation:
        return Observation(
            episode_id=self.episode_id,
            step=self.step_count,
            max_steps=self.max_steps,
            problem_id=self.current_problem["id"],
            difficulty=self.current_problem["difficulty"],
            flaw_type=self.current_problem["flaw_type"],
            description=self.current_problem["description"],
            flawed_code=self.current_problem["flawed_code"],
            hint_available=self.hint_used,
            hint=self.current_problem["hint"] if self.hint_used else None,
            cumulative_reward=round(self.cumulative_reward, 4),
            done=self.done,
            feedback=feedback,
        )
