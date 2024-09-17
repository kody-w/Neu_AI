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
            "description": "The StateClone skill allows you to save and load snapshots of the current state, which includes memory, context, and settings. You can also list all saved states. Use this skill to clone the state across instances or restore a previous state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["save", "load", "list"],
                        "description": "The action to perform. Choose 'save' to save the current state, 'load' to load a saved state into the current state, or 'list' to display all available saved states. This parameter is required."
                    },
                    "state_name": {
                        "type": "string",
                        "description": "The name of the state to save or load. This is required for 'save' and 'load' actions and is used as part of the filename when saving or loading states."
                    },
                    "memory": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array representing memory data to update the current state with before saving. Provide this when you want to modify the 'memory' part of the state prior to saving."
                    },
                    "context": {
                        "type": "object",
                        "description": "An object representing context data to update the current state with before saving. Provide this when you want to modify the 'context' part of the state prior to saving."
                    },
                    "settings": {
                        "type": "object",
                        "description": "An object representing settings data to update the current state with before saving. Provide this when you want to modify the 'settings' part of the state prior to saving."
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
    
    def perform(self, action, state_name=None, memory=None, context=None, settings=None):
        if memory is not None or context is not None or settings is not None:
            self.update_current_state(memory=memory, context=context, settings=settings)
        if action == "save":
            if not state_name:
                return json.dumps({"error": "The 'state_name' parameter is required for the 'save' action."})
            return self.save_state(state_name)
        elif action == "load":
            if not state_name:
                return json.dumps({"error": "The 'state_name' parameter is required for the 'load' action."})
            return self.load_state(state_name)
        elif action == "list":
            return self.list_states()
        else:
            return json.dumps({"error": "Invalid action. Please use 'save', 'load', or 'list'."})
    
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
        
        return json.dumps({"message": f"State saved successfully as '{file_name}'."})
    
    def load_state(self, state_name):
        state_files = [f for f in os.listdir(self.state_dir) if f.startswith(f"{state_name}_") and f.endswith(".json")]
        
        if not state_files:
            return json.dumps({"error": f"No saved states found for '{state_name}'."})
        
        latest_state_file = max(state_files)
        file_path = os.path.join(self.state_dir, latest_state_file)
        
        with open(file_path, 'r') as f:
            loaded_state = json.load(f)
        
        self.current_state = loaded_state["state"]
        return json.dumps({"message": f"State '{latest_state_file}' loaded successfully."})
    
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
        if memory is not None:
            self.current_state["memory"] = memory
        if context is not None:
            self.current_state["context"] = context
        if settings is not None:
            self.current_state["settings"] = settings
    
    def get_state_similarity(self, state1, state2):
        def compute_hash(obj):
            return hashlib.md5(json.dumps(obj, sort_keys=True).encode()).hexdigest()
    
        hash1 = compute_hash(state1)
        hash2 = compute_hash(state2)
        
        return 1 - (bin(int(hash1, 16) ^ int(hash2, 16)).count('1') / 128)
    
    def find_similar_states(self, threshold=0.9):
        state_files = [f for f in os.listdir(self.state_dir) if f.endswith(".json")]
        similar_states = []
    
        for file in state_files:
            file_path = os.path.join(self.state_dir, file)
            with open(file_path, 'r') as f:
                saved_state = json.load(f)["state"]
            
            similarity = self.get_state_similarity(self.current_state, saved_state)
            if similarity >= threshold:
                similar_states.append((file, similarity))
    
        return sorted(similar_states, key=lambda x: x[1], reverse=True)
