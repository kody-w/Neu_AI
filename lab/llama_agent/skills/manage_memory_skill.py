from skills.basic_skill import BasicSkill
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import json
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ManageMemorySkill(BasicSkill):
    def __init__(self):
        self.name = 'ManageMemory'
        self.metadata = {
            "name": self.name,
            "description": "Manages memories in a JSON-based storage system, supporting the CREATE operation. This skill allows saving the context of conversations to long-term memory for future references.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conversation_id": {
                        "type": "string",
                        "description": "The unique identifier of the conversation."
                    },
                    "session_id": {
                        "type": "string",
                        "description": "The unique identifier of the session."
                    },
                    "conversation_context": {
                        "type": "string",
                        "description": "The context or content of the conversation to be saved as a memory."
                    },
                    "companion_id": {
                        "type": "string",
                        "description": "The unique identifier of the AI companion."
                    },
                    "mood": {
                        "type": "string",
                        "description": "The current mood or emotional state of the AI companion."
                    },
                    "theme": {
                        "type": "string",
                        "description": "The main theme or topic of the conversation."
                    }
                },
                "required": ["conversation_id", "session_id", "conversation_context", "companion_id", "mood", "theme"]
            }
        }
        self.storage_file = 'memory.json'
        super().__init__(name=self.name, metadata=self.metadata)
        
        # Initialize Groq client
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")
        self.model = os.getenv('LLM_MODEL', 'llama3-groq-70b-8192-tool-use-preview')
        self.chatbot = ChatGroq(model=self.model, groq_api_key=self.groq_api_key)

    def perform(self, conversation_id: str, session_id: str, conversation_context: str, companion_id: str, mood: str, theme: str) -> str:
        try:
            return self.create(conversation_id, session_id, conversation_context, companion_id, mood, theme)
        except Exception as e:
            return f"An error occurred while managing memory: {str(e)}"

    def _load_memory(self):
        if not os.path.exists(self.storage_file):
            return {}
        with open(self.storage_file, 'r') as file:
            return json.load(file)

    def _save_memory(self, memory):
        with open(self.storage_file, 'w') as file:
            json.dump(memory, file, indent=2)

    def create(self, conversation_id: str, session_id: str, conversation_context: str, companion_id: str, mood: str, theme: str) -> str:
        memory = self._load_memory()
        new_memory_id = str(uuid.uuid4())
        memory[new_memory_id] = {
            "conversation_id": conversation_id,
            "session_id": session_id,
            "message": conversation_context,
            "companion_id": companion_id,
            "mood": mood,
            "theme": theme,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "time": datetime.now().strftime('%H:%M:%S')
        }
        self._save_memory(memory)
        
        # Use Groq to generate a concise summary of the saved memory
        messages = [
            SystemMessage(content="You are an AI assistant tasked with summarizing a newly created memory. Provide a brief, meaningful summary of the memory that has just been saved."),
            HumanMessage(content=f"A new memory has been saved with the following details:\n\n{json.dumps(memory[new_memory_id], indent=2)}\n\nPlease provide a concise summary of this memory.")
        ]

        try:
            response = self.chatbot.invoke(messages)
            return f"Memory saved successfully. Summary: {response.content}"
        except Exception as e:
            return f"Memory saved, but an error occurred while generating the summary: {str(e)}"

# Example usage:
# manage_memory_skill = ManageMemorySkill()
# result = manage_memory_skill.perform(
#     conversation_id="conv123",
#     session_id="sess456",
#     conversation_context="We discussed the importance of AI ethics.",
#     companion_id="ai789",
#     mood="thoughtful",
#     theme="AI Ethics"
# )
# print(result)