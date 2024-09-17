#!/bin/bash

# Create a virtual environment and install any dependencies (if needed)
# Uncomment these lines if you want to create and activate a virtual environment
# python3 -m venv venv
# source venv/bin/activate

# Ensure the directory for state snapshots exists
STATE_DIR="state_snapshots"
if [ ! -d "$STATE_DIR" ]; then
    mkdir "$STATE_DIR"
fi

# Run the Python script that tests the StateCloneSkill class
python3 << EOF
import json
import os
import hashlib
import time
from skills.basic_skill import BasicSkill

class StateCloneSkill(BasicSkill):
    def __init__(self):
        self.name = 'StateClone'
        self.metadata = {
            "name": self.name,
            "description": "Clones the current snapshot of state across instances for approximate similarity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["save", "load", "list"],
                        "description": "Action to perform: save current state, load a state, or list available states."
                    },
                    "state_name": {
                        "type": "string",
                        "description": "Name of the state to save or load (required for save and load actions)."
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        self.state_dir = 'state_snapshots'
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)
        
        self.current_state = {
            "memory": [],
            "context": {},
            "settings": {}
        }

    def perform(self, action, state_name=None):
        if action == "save":
            if not state_name:
                return json.dumps({"error": "state_name is required for save action"})
            return self.save_state(state_name)
        elif action == "load":
            if not state_name:
                return json.dumps({"error": "state_name is required for load action"})
            return self.load_state(state_name)
        elif action == "list":
            return self.list_states()
        else:
            return json.dumps({"error": "Invalid action. Use 'save', 'load', or 'list'."})

    def save_state(self, state_name):
        timestamp = int(time.time())
        state_to_save = {
            "timestamp": timestamp,
            "state": self.current_state
        }
        
        file_name = f"{state_name}_{timestamp}.json"
        file_path = os.path.join(self.state_dir, file_name)
        
        with open(file_path, 'w') as f:
            json.dump(state_to_save, f, indent=2)
        
        return json.dumps({"message": f"State saved successfully as {file_name}"})

    def load_state(self, state_name):
        state_files = [f for f in os.listdir(self.state_dir) if f.startswith(f"{state_name}_") and f.endswith(".json")]
        
        if not state_files:
            return json.dumps({"error": f"No saved states found for {state_name}"})
        
        latest_state_file = max(state_files)
        file_path = os.path.join(self.state_dir, latest_state_file)
        
        with open(file_path, 'r') as f:
            loaded_state = json.load(f)
        
        self.current_state = loaded_state["state"]
        return json.dumps({"message": f"State {latest_state_file} loaded successfully"})

    def list_states(self):
        state_files = [f for f in os.listdir(self.state_dir) if f.endswith(".json")]
        states = {}
        
        for file in state_files:
            state_name = file.split('_')[0]
            if state_name not in states:
                states[state_name] = []
            states[state_name].append(file)
        
        return json.dumps(states, indent=2)

    def update_current_state(self, memory=None, context=None, settings=None):
        if memory:
            self.current_state["memory"] = memory
        if context:
            self.current_state["context"] = context
        if settings:
            self.current_state["settings"] = settings

# Initialize the skill
state_clone_skill = StateCloneSkill()

# Update the current state with some dummy data
state_clone_skill.update_current_state(
    memory=["Remember to test save and load functionality"],
    context={"user": "test_user", "session": 1},
    settings={"theme": "dark"}
)

# Perform a 'save' action
output1 = state_clone_skill.perform(action="save", state_name="test_state")
print(output1)

# List available states
output2 = state_clone_skill.perform(action="list")
print(output2)

# Update the current state with different data
state_clone_skill.update_current_state(
    memory=["New memory to test state cloning"],
    context={"user": "test_user", "session": 2},
    settings={"theme": "light"}
)

# Save the updated state
output3 = state_clone_skill.perform(action="save", state_name="test_state_2")
print(output3)

# Load the previous state
output4 = state_clone_skill.perform(action="load", state_name="test_state")
print(output4)

# List available states again to verify both are saved
output5 = state_clone_skill.perform(action="list")
print(output5)

# Check if the current state was restored correctly
print(state_clone_skill.current_state)

EOF

# Expected output strings
expected_output1='{"message": "State saved successfully as test_state'
expected_output2='{"test_state": ['
expected_output3='{"message": "State saved successfully as test_state_2'
expected_output4='{"message": "State test_state'
expected_output5='{"test_state": ['
expected_state='{"memory": ["Remember to test save and load functionality"], "context": {"user": "test_user", "session": 1}, "settings": {"theme": "dark"}}'

# Check output
if [[ $(python3 test.sh | grep "$expected_output1") ]]; then
    echo "Test 1 Passed: Save state"
else
    echo "Test 1 Failed: Save state"
fi

if [[ $(python3 test.sh | grep "$expected_output2") ]]; then
    echo "Test 2 Passed: List states"
else
    echo "Test 2 Failed: List states"
fi

if [[ $(python3 test.sh | grep "$expected_output3") ]]; then
    echo "Test 3 Passed: Save second state"
else
    echo "Test 3 Failed: Save second state"
fi

if [[ $(python3 test.sh | grep "$expected_output4") ]]; then
    echo "Test 4 Passed: Load state"
else
    echo "Test 4 Failed: Load state"
fi

if [[ $(python3 test.sh | grep "$expected_output5") ]]; then
    echo "Test 5 Passed: List states after second save"
else
    echo "Test 5 Failed: List states after second save"
fi

if [[ $(python3 test.sh | grep "$expected_state") ]]; then
    echo "Test 6 Passed: Current state matches expected"
else
    echo "Test 6 Failed: Current state does not match expected"
fi
