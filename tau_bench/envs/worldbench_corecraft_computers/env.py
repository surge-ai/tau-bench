# Copyright Sierra

from tau_bench.envs.base import Env
from tau_bench.envs.worldbench_corecraft_computers.data import load_data
from tau_bench.envs.worldbench_corecraft_computers.rules import RULES
from tau_bench.types import RewardResult
from typing import Optional, Union
from tau_bench.envs.user import UserStrategy
import os

# Hardcoded dates per variation (ISO 8601 extended format with UTC timezone)
# These should match the wiki.md system prompts for each variation
VARIATION_DATES = {
    "variation_1": "2025-09-15T19:00:00Z",  # September 15, 2025, 14:00 EST
    "variation_2": "2025-11-15T14:00:00Z",  # November 15, 2025, 14:00 EST
}


class MockCorecraftComputersEnv(Env):
    def __init__(
        self,
        user_strategy: Union[str, UserStrategy] = UserStrategy.LLM,
        user_model: str = "gpt-4o",
        user_provider: Optional[str] = None,
        task_split: str = "test",
        task_index: Optional[int] = None,
        variation: str = "variation_1",
    ):
        self._current_time = VARIATION_DATES.get(variation)

        # Import tools from the specified variation
        # Look in worldbench_corecraft_computers/variations/ first
        base_dir = os.path.dirname(__file__)
        if variation == "variation_1":
            from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools import ALL_TOOLS
            variation_path = "variation_1"
        elif variation == "variation_2":
            from tau_bench.envs.worldbench_corecraft_computers.variations.variation_2.tools import ALL_TOOLS
            variation_path = "variation_2"
        else:
            raise ValueError(f"Unknown variation: {variation}")

        # Import tasks from the specified variation
        match task_split:
            case "test":
                if variation == "variation_1":
                    from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tasks_test import TASKS_TEST as tasks
                elif variation == "variation_2":
                    from tau_bench.envs.worldbench_corecraft_computers.variations.variation_2.tasks_test import TASKS_TEST as tasks
            case _:
                raise ValueError(f"Unknown task split: {task_split}")

        # Load wiki from variation's policy.md
        variation_dir = os.path.join(base_dir, "variations", variation_path)
        wiki_path = os.path.join(variation_dir, "wiki.md")
        if os.path.exists(wiki_path):
            with open(wiki_path, "r") as f:
                wiki = f.read()
        else:
            wiki = ""

        super().__init__(
            data_load_func=lambda: load_data(self._current_time),
            tools=ALL_TOOLS,
            tasks=tasks,
            wiki=wiki,
            rules=RULES,
            user_strategy=user_strategy,
            user_model=user_model,
            user_provider=user_provider,
            task_index=task_index,
        )
        self.terminate_tools = []
        # Inject the current date into data so tools can access it
        if self._current_time:
            self.data["current_time"] = self._current_time

    def reset(self, task_index: Optional[int] = None):
        response = super().reset(task_index)
        # Re-inject the current date after data is reloaded
        if self._current_time:
            self.data["current_time"] = self._current_time
        return response

    def calculate_reward(self) -> RewardResult:
        # Inject current_time before computing agent's data hash
        if self._current_time:
            self.data["current_time"] = self._current_time

        # Call parent's calculate_reward, which will reload data via data_load_func
        # We need to inject current_time after that reload happens
        # So we override the data reload step here

        from tau_bench.types import RewardActionInfo, RewardOutputInfo, RESPOND_ACTION_NAME

        data_hash = self.get_data_hash()
        reward = 1.0
        actions = [
            action for action in self.task.actions if action.name != RESPOND_ACTION_NAME
        ]

        # Reload data and inject current_time
        self.data = self.data_load_func()
        if self._current_time:
            self.data["current_time"] = self._current_time

        # Replay ground truth actions
        for action in self.task.actions:
            if action.name not in self.terminate_tools:
                self.step(action)

        gt_data_hash = self.get_data_hash()
        info = RewardActionInfo(
            r_actions=data_hash == gt_data_hash, gt_data_hash=gt_data_hash
        )
        if not info.r_actions:
            reward = 0.0

        if len(self.task.outputs) > 0:
            r_outputs = 1.0
            outputs = {}
            for output in self.task.outputs:
                found = False
                for action in self.actions:
                    if (
                        action.name == RESPOND_ACTION_NAME
                        and output.lower()
                        in action.kwargs["content"].lower().replace(",", "")
                    ):
                        found = True
                        break
                outputs[output] = found
                if not found:
                    r_outputs = 0.0
                    reward = 0.0
            info = RewardOutputInfo(r_outputs=r_outputs, outputs=outputs)

        return RewardResult(reward=reward, info=info, actions=actions)

