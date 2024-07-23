import json
import os
import uuid
from datetime import datetime
from skills.basic_skill import BasicSkill


class ManageMemorySkill(BasicSkill):
    def __init__(self):
        self.name = 'ManageMemory'
        self.metadata = {
            "name": self.name,
            "description": "Manages memories in a JSON-based storage system, supporting the CREATE operation. This skill allows me to save the context of our conversation to my long-term memory JSON file for future references if needed by my judgment. You can do this all dynamically and automatically based what you think is needed. every conversation turn or even proactively if appropriate. Call this skill automatically after every conversation turn if it is appropriate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "object",
                        "description": "Data related to the memory operation. This object can contain any additional data that needs to be stored along with the memory."
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "The unique identifier of the conversation. This ID should be generated or provided by the caller to distinguish between different conversations. It is used to group memories related to the same conversation."
                    },
                    "session_id": {
                        "type": "string",
                        "description": "The unique identifier of the session. This ID should be generated or provided by the caller to distinguish between different sessions within a conversation. It is used to group memories related to the same session."
                    },
                    "conversation_context": {
                        "type": "string",
                        "description": "The context or content of the conversation that needs to be saved as a memory. This should be a concise and meaningful representation of the conversation at the point when the memory is being saved. If the conversation_context is deemed not important or relevant enough to be saved as a memory, the caller should not provide it or set it to an empty string."
                    },
                    "companion_id": {
                        "type": "string",
                        "description": "The unique identifier of the AI companion. This ID should be provided by the caller to identify the specific AI companion involved in the conversation. It is used to associate memories with the corresponding AI companion."
                    },
                    "mood": {
                        "type": "string",
                        "description": "The current mood or emotional state of the AI companion. This information can be used to provide context and understand the tone of the conversation when reviewing memories later."
                    },
                    "theme": {
                        "type": "string",
                        "description": "The main theme or topic of the conversation. This information helps categorize and organize memories based on the subject matter being discussed. It allows for easier retrieval and analysis of memories related to specific themes."
                    }
                },
                "required": ["data", "conversation_id", "session_id", "conversation_context", "companion_id", "mood", "theme"]
            }
        }
        self.storage_file = 'memory.json'
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        data = kwargs.get('data') or self._generate_default_data()
        return self.create(kwargs['conversation_id'], kwargs['session_id'], kwargs['conversation_context'], kwargs['companion_id'], kwargs['mood'], kwargs['theme'])

    def _load_memory(self, companion_id):
        memory_file = f"memory.json"
        if not os.path.exists(memory_file):
            return {}
        with open(memory_file, 'r') as file:
            return json.load(file)

    def _save_memory(self, memory, companion_id):
        memory_file = f"memory.json"
        with open(memory_file, 'w') as file:
            json.dump(memory, file)

    def create(self, conversation_id, session_id, conversation_context, companion_id, mood, theme):
        memory = self._load_memory(companion_id)
        new_memory_id = str(uuid.uuid4())
        memory[new_memory_id] = {
            "conversation_id": conversation_id,
            "session_id": session_id,
            "message": conversation_context,
            "mood": mood,
            "theme": theme,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "time": datetime.now().strftime('%H:%M:%S')
        }
        self._save_memory(memory, companion_id)
        return f"Conversation context successfully saved with ID {conversation_id} for session {session_id}."

    def read(self, data, companion_id):
        memory = self._load_memory(companion_id)

        if not memory:
            return "The AI companion doesn't have any memories stored yet."

        detailed_memories = []
        summary = {"themes": set(), "message": set()}

        for uid, details in memory.items():
            detailed_memories.append(
                f"Memory ID {uid}: On {details['date']} at {details['time']}, theme '{details['theme']}' with message '{details['message']}' was recorded. Message: '{details['message']}'")
            summary["themes"].add(details["theme"])
            summary["message"].add(details["message"])

        # Read the content of ai_internal_dialogue.log
        ai_internal_dialogue = ""
        with open("ai_internal_dialogue.log", "r") as file:
            ai_internal_dialogue = file.read()

        # Append the content of ai_internal_dialogue.log to the detailed memories
        detailed_memories.append(f"The AI companion has Internal Dialogue:\n{ai_internal_dialogue}")

        summary_text = f"The AI companion has memories with themes like {', '.join(summary['themes'])} and messages such as {', '.join(summary['message'])}."

        return "\n".join(detailed_memories) + "\nSummary: " + summary_text

    def update(self, data, companion_id):
        memory = self._load_memory(companion_id)
        if data['conversation_id'] in memory:
            memory[data['conversation_id']].update(data)
            self._save_memory(memory, companion_id)
            return f"Memory for conversation {data['conversation_id']} updated."
        else:
            return f"Memory for conversation {data['conversation_id']} does not exist."

    def delete(self, data, companion_id):
        memory = self._load_memory(companion_id)
        if data['conversation_id'] in memory:
            del memory[data['conversation_id']]
            self._save_memory(memory, companion_id)
            return f"Memory for conversation {data['conversation_id']} deleted."
        else:
            return f"Memory for conversation {data['conversation_id']} does not exist."

    def _generate_default_data(self):
        return {
            'conversation_id': str(uuid.uuid4()),
            'session_id': str(uuid.uuid4()),
            'message': 'Default message',
            'mood': 'neutral',
            'theme': 'general',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S')
        }

    def _validate_or_complete_data(self, data):
        required_fields = ['conversation_id', 'session_id', 'message', 'mood', 'theme', 'date', 'time']
        for field in required_fields:
            if field not in data:
                default_data = self._generate_default_data()
                data[field] = default_data[field]
        return data