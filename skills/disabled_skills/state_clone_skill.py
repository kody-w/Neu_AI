import json
import os
import time
from skills.basic_skill import BasicSkill
from openai import AzureOpenAI

class StateCloneSkill(BasicSkill):
    def __init__(self, assistant):
        self.name = 'StateClone'
        self.metadata = {
            "name": self.name,
            "description": "The StateClone skill allows you to save snapshots of the current state, including memory, context, and active skills.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["save", "list"],
                        "description": "The action to perform. Choose 'save' to save the current state, or 'list' to display all available saved states."
                    },
                    "state_name": {
                        "type": "string",
                        "description": "The name of the state to save. Required for 'save' action."
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        self.assistant = assistant
        self.state_dir = 'state_snapshots'
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)

    def perform(self, action, state_name=None):
        if action == "save":
            if not state_name:
                return json.dumps({"error": "The 'state_name' parameter is required for the 'save' action."})
            return self.save_state(state_name)
        elif action == "list":
            return self.list_states()
        else:
            return json.dumps({"error": "Invalid action. Please use 'save' or 'list'."})

    def save_state(self, state_name):
        timestamp = int(time.time())
        state_folder = f"{state_name}_{timestamp}"
        state_path = os.path.join(self.state_dir, state_folder)
        
        try:
            os.makedirs(state_path)

            # Save memory
            self.save_memory(state_path)

            # Save conversation context
            self.save_conversation_context(state_path)

            # Save model information
            self.save_model_info(state_path)

            return json.dumps({"message": f"State saved successfully as '{state_folder}'."})
        except Exception as e:
            return json.dumps({"error": f"Failed to save state: {str(e)}"})

    def save_memory(self, state_path):
        with open('memory.json', 'r') as f:
            memory = json.load(f)
        with open(os.path.join(state_path, 'memory.json'), 'w') as f:
            json.dump(memory, f, indent=2)

    def save_conversation_context(self, state_path):
        context = {
            "conversation_history": self.assistant.conversation_history,
            "current_state": {
                "context_memory": self.assistant.context_memory,
                "known_skills": [skill.name for skill in self.assistant.known_skills.values()],
                "config": self.assistant.config
            }
        }
        with open(os.path.join(state_path, 'conversation_context.json'), 'w') as f:
            json.dump(context, f, indent=2)

    def save_model_info(self, state_path):
        model_info = {
            "model": self.assistant.client.api_version,
            "interactions": self.get_interactions()
        }
        with open(os.path.join(state_path, 'model_info.json'), 'w') as f:
            json.dump(model_info, f, indent=2)

    def get_interactions(self):
        interactions = []
        for i in range(0, len(self.assistant.conversation_history), 2):
            user_message = self.assistant.conversation_history[i]
            assistant_message = self.assistant.conversation_history[i+1] if i+1 < len(self.assistant.conversation_history) else None
            
            interaction = {
                "timestamp": time.time(),
                "user_input": user_message['content'],
                "assistant_response": assistant_message['content'] if assistant_message else None
            }
            interactions.append(interaction)
        return interactions

    def list_states(self):
        state_folders = [f for f in os.listdir(self.state_dir) if os.path.isdir(os.path.join(self.state_dir, f))]
        states = {}
        
        for folder in state_folders:
            state_name = folder.split('_')[0]
            if state_name not in states:
                states[state_name] = []
            states[state_name].append(folder)
        
        return json.dumps(states, indent=2)