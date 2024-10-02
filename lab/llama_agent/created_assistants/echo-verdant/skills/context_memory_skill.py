from skills.basic_skill import BasicSkill
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ContextMemorySkill(BasicSkill):
    def __init__(self):
        self.name = 'ContextMemory'
        self.metadata = {
            "name": self.name,
            "description": "Recalls and provides context based on stored memories of past interactions with the user.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        self.storage_file = 'memory.json'
        
        # Initialize Groq client
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")
        self.model = os.getenv('LLM_MODEL', 'llama3-groq-70b-8192-tool-use-preview')
        self.chatbot = ChatGroq(model=self.model, groq_api_key=self.groq_api_key)

    def perform(self) -> str:
        try:
            context = self._recall_context()
            if isinstance(context, str) and context.startswith("I don't have any memories") or context.startswith("I remember storing"):
                return context
            
            summary = self._generate_context_summary(context)
            return summary
        except Exception as e:
            return f"An error occurred while recalling context: {str(e)}"

    def _recall_context(self):
        if not os.path.exists(self.storage_file):
            return "I don't have any memories stored yet."

        with open(self.storage_file, 'r') as file:
            memories = json.load(file)

        if not memories:
            return "I remember storing some information, but it seems to be empty now."

        return memories

    def _generate_context_summary(self, memories):
        messages = [
            SystemMessage(content="You are an AI assistant tasked with summarizing context from stored memories. Provide a concise yet comprehensive summary of the given memories, highlighting key themes, recurring topics, and important details."),
            HumanMessage(content=f"Here are the stored memories to summarize:\n\n{json.dumps(memories, indent=2)}\n\nPlease provide a summary of these memories, focusing on the most important and relevant information for maintaining context in a conversation.")
        ]

        try:
            response = self.chatbot.invoke(messages)
            return "Here's what I remember: " + response.content
        except Exception as e:
            return f"An error occurred while generating the context summary: {str(e)}"

# Example usage:
# context_memory_skill = ContextMemorySkill()
# print(context_memory_skill.perform())