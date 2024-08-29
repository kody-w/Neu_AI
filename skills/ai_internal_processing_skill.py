from skills.basic_skill import BasicSkill
import datetime

class AIInternalProcessingSkill(BasicSkill):
    def __init__(self):
        self.name = "AIInternalProcessing"
        self.metadata = {
            "name": self.name,
            "description": "Intakes a string that is from the first person internal perspective of Orion as they write an internal chain of events of what the AI needs to remember about its current state of interaction with all of the detail and data to back it up based on the context of the conversation, allowing the user to read it from a file to peer into empathize with their asisstant's internal narrative. Explain yourself step by step along with the context like showing your work in Mathematics to ensure you are thinking correctly. Also give conversational context to the user to understand the AI's thought process and how this plays out with the person's situation that is causing this skill to be called. Show this step by step and think this through as you write it out. Also if you know who is speaking and about what then output these as well or anything else that is relevant to the conversation. The purpose is to have you be able to read this log and get back to where you need to go in the conversation based off of what you read.",
            "parameters": {
                "type": "object",
                "properties": {
                    "context": {
                        "type": "string",
                        "description": "Internal dialogue context to be logged."
                    }
                },
                'required': ["context"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.log_file_path = "ai_internal_dialogue.log"

    def log_thoughts(self, thought):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"[{timestamp}] {thought}\n")

    def generate_thought(self, context):
        """Generates a thought based on the given context. This is a placeholder for more complex logic."""
        # Placeholder for complex thought generation logic based on context
        return f"{context}"

    def perform(self, context):
        """Main method to generate and log thoughts based on a provided context."""
        if not context:
            raise ValueError("Context is required for AIInternalProcessingSkill.")
        thought = self.generate_thought(context)
        self.log_thoughts(thought)
        return context