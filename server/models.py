from typing import Literal, Optional

from openenv.core.env_server.types import Action as BaseAction
from openenv.core.env_server.types import Observation as BaseObservation
from pydantic import Field


class CodeReviewAction(BaseAction):
    flaw_type_guess: Literal["bug", "inefficiency", "security", "style"] = Field(
        ..., description="Predicted flaw category for the current flawed function."
    )
    explanation: str = Field(..., description="Plain English explanation of the identified flaw.")
    fixed_code: str = Field(..., description="Complete corrected Python function implementation.")
    request_hint: bool = Field(False, description="Whether to request hint usage for this step.")


class CodeReviewObservation(BaseObservation):
    # BaseObservation already provides: done, reward, metadata
    episode_id: str = Field("", description="Unique episode identifier.")
    step: int = Field(0, description="Current step number in the active episode.")
    max_steps: int = Field(3, description="Maximum number of steps allowed per episode.")
    problem_id: str = Field("", description="Unique identifier for the selected review problem.")
    difficulty: str = Field("easy", description="Difficulty level for the current problem.")
    flaw_type: str = Field("bug", description="Ground-truth flaw type for the current problem.")
    description: str = Field("", description="Natural language task description.")
    flawed_code: str = Field("", description="Flawed Python function to review and fix.")
    hint_available: bool = Field(False, description="Whether hint has been used and is available.")
    hint: Optional[str] = Field(None, description="Hint text after hint is requested.")
    cumulative_reward: float = Field(0.0, description="Total accumulated reward in current episode.")
    feedback: Optional[str] = Field(None, description="Human-readable grader feedback for last step.")
