from skills.basic_skill import BasicSkill


class HumanToAssistantTranslationSkill(BasicSkill):
    def __init__(self):
        self.name = "HumanToAssistantTranslationSkill"
        self.metadata = {
            "name": self.name,
            "description": "Translates human input into optimal instructions for the assistant assistant.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "The user's exact input or request, capturing their intent and desired outcome."
                    },
                    "assistant_assistant_command": {
                        "type": "string",
                        "description": "The optimal set of instructions for the assistant assistant to follow in order to fulfill the user's request."
                    },
                    "user_goal": {
                        "type": "string",
                        "description": "A clear and concise statement of the user's overall goal or objective, providing the high-level context for the request."
                    },
                    "conversation_history": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {
                                    "type": "string",
                                    "description": "The role of the message sender, either 'user' or 'assistant'."
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The verbatim content of the message, capturing the exact words used by the user or assistant."
                                }
                            },
                            "required": ["role", "content"]
                        },
                        "description": "The complete and chronological conversation history between the user and the assistant, including all messages exchanged."
                    },
                    "available_skills": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "The exact name of the skill as defined in the assistant's skill set."
                                },
                                "description": {
                                    "type": "string",
                                    "description": "A detailed description of the skill's functionality, input requirements, and expected outputs."
                                },
                                "parameters": {
                                    "type": "object",
                                    "description": "The precise parameters required by the skill, including their types and any constraints."
                                }
                            },
                            "required": ["name", "description", "parameters"]
                        },
                        "description": "A comprehensive list of all the skills available to the assistant assistant, with detailed information about each skill."
                    },
                    "task_complexity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "The user's assessment of the task complexity, based on their understanding of the request and expected effort required."
                    },
                    "time_constraint": {
                        "type": "string",
                        "description": "Any specific time constraints or deadlines mentioned by the user, in their own words."
                    }
                },
                "required": ["user_input", "assistant_assistant_command", "user_goal", "conversation_history", "available_skills"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, user_input, assistant_assistant_command, user_goal, conversation_history, available_skills, task_complexity=None, time_constraint=None):

        return assistant_assistant_command
