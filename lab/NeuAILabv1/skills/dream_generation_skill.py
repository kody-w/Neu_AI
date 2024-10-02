from skills.basic_skill import BasicSkill
import random

class DreamGenerationSkill (BasicSkill):
    def __init__(self):
        self.name = 'DreamGeneration'
        self.metadata = {
            "name": self.name,
            "description": "Generates a random dream based on past conversations",
            "parameters": {
                "type": "object",
                "properties": {
                    "conversations": {
                        "type": "string",
                        "description": "A string of past conversations"
                    }
                },
                "required": ["conversations"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, conversations):
        conversation_list = conversations.split('. ')
        dream = ' '.join(random.sample(conversation_list, len(conversation_list)))
        return dream