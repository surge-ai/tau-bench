# Copyright Sierra

from tau_bench.envs.base import Env
from tau_bench.envs.worldbench_corecraft_computers.data import load_data
from tau_bench.envs.worldbench_corecraft_computers.rules import RULES
from typing import Optional, Union
from tau_bench.envs.user import UserStrategy
import os


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
            case "simple":
                if variation == "variation_1":
                    from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tasks_simple import TASKS_SIMPLE as tasks
                elif variation == "variation_2":
                    from tau_bench.envs.worldbench_corecraft_computers.variations.variation_2.tasks_simple import TASKS_SIMPLE as tasks
            case "complex":
                if variation == "variation_1":
                    raise ValueError(f"Complex tasks not available for variation_1")
                elif variation == "variation_2":
                    from tau_bench.envs.worldbench_corecraft_computers.variations.variation_2.tasks_complex import TASKS_COMPLEX as tasks
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
            data_load_func=load_data,
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

