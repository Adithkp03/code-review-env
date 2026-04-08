import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from envs.code_review_env import CodeReviewEnv
from server.models import CodeReviewAction, CodeReviewObservation


class CodeReviewEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._inner = CodeReviewEnv(max_steps=3, randomize=True)

    def reset(self) -> CodeReviewObservation:
        obs = self._inner.reset()
        return CodeReviewObservation(
            done=obs.done,
            reward=0.0,
            episode_id=obs.episode_id,
            step=obs.step,
            max_steps=obs.max_steps,
            problem_id=obs.problem_id,
            difficulty=obs.difficulty,
            flaw_type=obs.flaw_type,
            description=obs.description,
            flawed_code=obs.flawed_code,
            hint_available=obs.hint_available,
            hint=obs.hint,
            cumulative_reward=obs.cumulative_reward,
            feedback=obs.feedback,
        )

    def step(self, action: CodeReviewAction) -> CodeReviewObservation:
        # Convert server Action to internal Action
        from models import Action as InternalAction

        internal_action = InternalAction(
            flaw_type_guess=action.flaw_type_guess,
            explanation=action.explanation,
            fixed_code=action.fixed_code,
            request_hint=action.request_hint,
        )
        obs, reward_val, done, info = self._inner.step(internal_action)
        return CodeReviewObservation(
            done=done,
            reward=reward_val,
            metadata={"grade": info.get("grade", {}), "reward_breakdown": info.get("reward_breakdown", {})},
            episode_id=obs.episode_id,
            step=obs.step,
            max_steps=obs.max_steps,
            problem_id=obs.problem_id,
            difficulty=obs.difficulty,
            flaw_type=obs.flaw_type,
            description=obs.description,
            flawed_code=obs.flawed_code,
            hint_available=obs.hint_available,
            hint=obs.hint,
            cumulative_reward=obs.cumulative_reward,
            feedback=obs.feedback,
        )

    @property
    def state(self) -> State:
        try:
            s = self._inner.state()
            return State(
                episode_id=s.episode_id,
                step_count=s.step,
            )
        except RuntimeError:
            return State(episode_id="", step_count=0)
