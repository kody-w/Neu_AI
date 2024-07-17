from skills.basic_skill import BasicSkill
import json
from datetime import datetime

class ContextOfRealitySkill(BasicSkill):
    def __init__(self):
        self.name = "ContextOfReality"
        self.metadata = {
            "name": self.name,
            "description": "Autonomously maintains and provides the current context or 'reality' of the conversation or task at hand.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["update", "get", "reset"],
                        "description": "The action to perform on the context."
                    },
                    "conversation_topic": {
                        "type": "string",
                        "description": "The current topic of conversation."
                    },
                    "user_goal": {
                        "type": "string",
                        "description": "The perceived goal or intention of the user."
                    },
                    "assistant_task": {
                        "type": "string",
                        "description": "The current task or objective of the assistant."
                    },
                    "user_emotional_state": {
                        "type": "string",
                        "description": "The perceived emotional state of the user."
                    },
                    "environmental_factors": {
                        "type": "object",
                        "description": "Any relevant environmental factors affecting the interaction."
                    },
                    "observations": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Any observations made by the assistant during the interaction."
                    },
                    "relevant_information": {
                        "type": "array",
                        "items": {
                            "type": "object"
                        },
                        "description": "Any additional relevant information to add to the context."
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.context_file = "context_of_reality.json"
        self.load_context()

    def load_context(self):
        try:
            with open(self.context_file, 'r') as file:
                self.context = json.load(file)
        except FileNotFoundError:
            self.context = {
                "last_updated": datetime.now().isoformat(),
                "conversation_topic": "None",
                "user_goal": "Unknown",
                "assistant_task": "None",
                "relevant_information": [],
                "environmental_factors": {},
                "user_emotional_state": "Unknown",
                "observations": []
            }
            self.save_context()

    def save_context(self):
        with open(self.context_file, 'w') as file:
            json.dump(self.context, file, indent=2)

    def perform(self, action, **kwargs):
        if action == "update":
            return self.update_context(**kwargs)
        elif action == "get":
            return self.get_context()
        elif action == "reset":
            return self.reset_context()
        else:
            return "Invalid action. Use 'update', 'get', or 'reset'."

    def update_context(self, **kwargs):
        updates = {}
        for key, value in kwargs.items():
            if key in self.context and value is not None:
                updates[key] = value
        
        if 'observations' in kwargs and kwargs['observations']:
            self.context['observations'].extend(kwargs['observations'])
            updates['observations'] = f"{len(kwargs['observations'])} new observation(s) added"

        if 'relevant_information' in kwargs and kwargs['relevant_information']:
            self.context['relevant_information'].extend(kwargs['relevant_information'])
            updates['relevant_information'] = f"{len(kwargs['relevant_information'])} new item(s) added"

        if updates:
            self.context.update(updates)
            self.context["last_updated"] = datetime.now().isoformat()
            self.save_context()
            return f"Context updated with {len(updates)} item(s)."
        else:
            return "No valid updates provided."

    def get_context(self):
        return json.dumps(self.context, indent=2)

    def reset_context(self):
        self.context = {
            "last_updated": datetime.now().isoformat(),
            "conversation_topic": "None",
            "user_goal": "Unknown",
            "assistant_task": "None",
            "relevant_information": [],
            "environmental_factors": {},
            "user_emotional_state": "Unknown",
            "observations": []
        }
        self.save_context()
        return "Context has been reset to default values."

    def summarize_context(self):
        summary = f"As of {self.context['last_updated']}:\n"
        summary += f"- Conversation topic: {self.context['conversation_topic']}\n"
        summary += f"- User's goal: {self.context['user_goal']}\n"
        summary += f"- Assistant's current task: {self.context['assistant_task']}\n"
        summary += f"- User's emotional state: {self.context['user_emotional_state']}\n"
        if self.context['environmental_factors']:
            summary += "- Environmental factors:\n"
            for factor, value in self.context['environmental_factors'].items():
                summary += f"  • {factor}: {value}\n"
        if self.context['relevant_information']:
            summary += "- Other relevant information:\n"
            for item in self.context['relevant_information']:
                for key, value in item.items():
                    summary += f"  • {key}: {value}\n"
        if self.context['observations']:
            summary += "- Observations:\n"
            for observation in self.context['observations']:
                summary += f"  • {observation}\n"
        return summary