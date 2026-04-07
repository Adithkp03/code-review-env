from typing import Literal, Optional

from pydantic import BaseModel


class Observation(BaseModel):
    episode_id: str
    step: int
    max_steps: int
    problem_id: str
    difficulty: Literal["easy", "medium", "hard"]
    flaw_type: Literal["bug", "inefficiency", "security", "style"]
    description: str
    flawed_code: str
    hint_available: bool
    hint: Optional[str]
    cumulative_reward: float
    done: bool
    feedback: Optional[str]


class Action(BaseModel):
    flaw_type_guess: Literal["bug", "inefficiency", "security", "style"]
    explanation: str
    fixed_code: str
    request_hint: bool = False


class State(BaseModel):
    episode_id: str
    problem_id: str
    step: int
    max_steps: int
    hint_used: bool
    cumulative_reward: float
    done: bool
    grade_history: list[dict]


class EpisodeResult(BaseModel):
    episode_id: str
    problem_id: str
    difficulty: str
    flaw_type: str
    total_reward: float
    steps_taken: int
    hint_used: bool
    passed_all_tests: bool
    final_grade: dict
