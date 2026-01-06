#!/usr/bin/env python3
"""Transform tasks_test.py into JSON format similar to the reference file."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List
import uuid

# Base paths
BASE_DIR = Path(__file__).parent
VARIATION_DIR = BASE_DIR / "tau_bench" / "envs" / "worldbench_corecraft_computers" / "variations" / "variation_1"
TOOLS_DIR = VARIATION_DIR / "tools"
TOOL_IMPLS_DIR = TOOLS_DIR / "tool_impls"
RULES_FILE = BASE_DIR / "tau_bench" / "envs" / "worldbench_corecraft_computers" / "rules.py"
WIKI_FILE = VARIATION_DIR / "wiki.md"

# UUID to reuse if it appears
REUSE_UUID = "c9b4de95-b0f6-4042-8e64-3cead283427b"
PLACEHOLDER_UUID = "UUID_PLACEHOLDER"

def read_file_content(file_path: Path) -> str:
    """Read file content."""
    if not file_path.exists():
        return ""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def get_tool_files() -> Dict[str, str]:
    """Get all tool files (excluding tests, __pycache__, etc.)."""
    tools = {}
    exclude = {
        "__init__.py",
        "__pycache__",
        "models.py",
        "tau_sqlite_utils.py",
        "tests",
        "tool_impls",
    }
    
    for file_path in TOOLS_DIR.rglob("*.py"):
        # Skip if in excluded directories or files
        if any(excluded in str(file_path.relative_to(TOOLS_DIR)) for excluded in exclude):
            continue
        
        # Only include files directly in tools directory (not subdirectories)
        if file_path.parent == TOOLS_DIR:
            rel_path = file_path.name
            tools[rel_path] = read_file_content(file_path)
    
    return tools

def get_tool_impl_files() -> Dict[str, str]:
    """Get all tool_impl files (excluding __pycache__, utils.py, etc.)."""
    tool_impls = {}
    exclude = {
        "__init__.py",
        "__pycache__",
        "utils.py",
    }
    
    for file_path in TOOL_IMPLS_DIR.rglob("*.py"):
        if any(excluded in str(file_path.relative_to(TOOL_IMPLS_DIR)) for excluded in exclude):
            continue
        
        if file_path.parent == TOOL_IMPLS_DIR:
            rel_path = file_path.name
            tool_impls[rel_path] = read_file_content(file_path)
    
    return tool_impls

def get_rules() -> str:
    """Get rules content."""
    return read_file_content(RULES_FILE)

def get_policy() -> str:
    """Get policy (wiki.md) content."""
    return read_file_content(WIKI_FILE)

def execute_actions_and_get_return_values(actions: List[Dict[str, Any]], data: Dict[str, Any], tools_map: Dict[str, Any]) -> List[str]:
    """Execute actions and return their return values as a list of JSON strings."""
    return_values = []
    
    for action in actions:
        action_name = action["name"]
        action_kwargs = action.get("arguments", {})
        
        if action_name in tools_map:
            try:
                tool_class = tools_map[action_name]
                # Execute the tool
                result = tool_class.invoke(data=data, **action_kwargs)
                # Store as JSON string (result is already a JSON string from tools)
                return_values.append(result)
            except Exception as e:
                # If execution fails, store error as JSON string
                error_result = json.dumps({"error": str(e)})
                return_values.append(error_result)
        else:
            # Unknown tool
            error_result = json.dumps({"error": f"Unknown tool: {action_name}"})
            return_values.append(error_result)
    
    return return_values

def transform_tasks() -> List[Dict[str, Any]]:
    """Transform tasks_test.py into JSON format."""
    # Try importing (requires venv)
    try:
        import sys
        sys.path.insert(0, str(BASE_DIR))
        from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tasks_test import TASKS_TEST
        from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools import ALL_TOOLS
        from tau_bench.envs.worldbench_corecraft_computers.data import load_data
        
        tasks = []
        for task in TASKS_TEST:
            tasks.append({
                "annotator": getattr(task, "annotator", "0"),
                "user_id": task.user_id,
                "instruction": task.instruction,
                "actions": [{"name": a.name, "kwargs": a.kwargs} for a in task.actions],
                "outputs": task.outputs
            })
    except Exception as e:
        print(f"Error: Could not import tasks: {e}")
        print("Make sure to activate the venv: source tau-bench/bin/activate")
        return []
    
    # Load data and create tools map
    data = load_data()
    tools_map = {
        tool.get_info()["function"]["name"]: tool for tool in ALL_TOOLS
    }
    
    workitems = []
    
    # Get metadata once (same for all workitems)
    tools = get_tool_files()
    tool_impls = get_tool_impl_files()
    rules = get_rules()
    policy = get_policy()
    
    for idx, task in enumerate(tasks, start=1):
        # Convert actions to JSON format
        action_sequence = []
        for action in task["actions"]:
            action_sequence.append({
                "name": action["name"],
                "arguments": action.get("kwargs", {})
            })
        
        # Execute actions and get return values
        # Reset data for each task to ensure clean state
        task_data = load_data()
        return_values = execute_actions_and_get_return_values(action_sequence, task_data, tools_map)
        
        # Create task answer
        task_answer = {
            "database_name": "corecraft.db",
            "database_interface_name": "variation_1",
            "task_id": f"task_{idx}",
            "user_id": task["user_id"],
            "task_instructions": task["instruction"],
            "task_action_sequence": json.dumps(action_sequence),
            "task_outputs": ", ".join(task["outputs"]) if task["outputs"] else "",
            "return_values": json.dumps(return_values),
            "intrinsic_complexity": "",
            "intrinsic_complexity_notes": ""
        }
        
        # Create workitem
        workitem = {
            "workItemId": str(uuid.uuid4()),
            "inputData": {},
            "metadata": {
                "tools": tools,
                "tool_impls": tool_impls,
                "rules": rules,
                "policy": policy,
            },
            "workflow": "NA",
            "locale": "en_US",
            REUSE_UUID: [
                {
                    "data": {
                        "taskAnswers": [task_answer]
                    }
                }
            ]
        }
        
        workitems.append(workitem)
    
    return workitems

def main():
    """Main function."""
    workitems = transform_tasks()
    
    if not workitems:
        print("No workitems generated. Exiting.")
        return
    
    # Create the output structure
    output = {
        "fileMetadata": {
            "simId": "NA",
            "channel": "tau-bench",
            "vendor": "3P",
            "batchFileId": str(uuid.uuid4()),
            "serviceOrderId": "SO-PLACEHOLDER",
            "workType": "NA",
            "workflowName": "Tau Bench Worldbench CoreCraft Computers",
            "sensitiveContentExposure": "NA",
            "locale": "en_US",
            "customerInputFileName": "worldbench_corecraft_computers_variation_1",
            "annotationType": "NA",
            "conventionLink": "NA",
            "inputDataType": "NA",
            "outputDataType": "NA",
            "customerID": "tau-bench",
            "ingestionDate": "2025-01-01",
            "workstream": "NA",
            "workitemsCount": len(workitems)
        },
        "workitems": workitems
    }
    
    # Write output
    output_file = BASE_DIR / "worldbench_corecraft_computers_variation_1_tasks_test.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Transformed {len(workitems)} tasks to {output_file}")

if __name__ == "__main__":
    main()

