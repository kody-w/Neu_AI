from skills.basic_skill import BasicSkill
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LongTermMemoryRecallSkill(BasicSkill):
    def __init__(self):
        self.name = 'LongTermMemoryRecall'
        self.metadata = {
            "name": self.name,
            "description": "Retrieves and summarizes stored long-term memories from past user interactions. Use this skill when you need to access historical context or recall previous conversations to inform current responses or decision-making processes.",
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
            memories = self._recall_long_term_memories()
            if isinstance(memories, str):
                return memories  # Return the error message if no memories found
            
            summary = self._generate_memory_summary(memories)
            return summary
        except Exception as e:
            return f"An error occurred while recalling long-term memories: {str(e)}"

    def _recall_long_term_memories(self):
        if not os.path.exists(self.storage_file):
            return "No long-term memories have been stored yet."

        with open(self.storage_file, 'r') as file:
            memories = json.load(file)

        if not memories:
            return "Long-term memory storage exists, but it appears to be empty."

        return memories

    def _generate_memory_summary(self, memories):
        messages = [
            SystemMessage(content="You are an AI assistant tasked with summarizing long-term memories. Provide a concise yet comprehensive summary of the given memories, highlighting key themes, recurring topics, and important details."),
            HumanMessage(content=f"Here are the long-term memories to summarize:\n\n{json.dumps(memories, indent=2)}\n\nPlease provide a summary of these memories, focusing on the most important and relevant information.")
        ]

        try:
            response = self.chatbot.invoke(messages)
            return response.content
        except Exception as e:
            return f"An error occurred while generating the memory summary: {str(e)}"

# Example usage:
# long_term_memory_recall_skill = LongTermMemoryRecallSkill()
# print(long_term_memory_recall_skill.perform())