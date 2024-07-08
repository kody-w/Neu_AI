import json
import os
from skills.basic_skill import BasicSkill

class ContextMemorySkill(BasicSkill):
    def __init__(self):
        self.name = 'ContextMemory'
        self.metadata = {
            "name": self.name,
            "description": "Recalls and provides context based on stored memories of the past interactions with the user.",
        }
        self.storage_file = 'memory.json'
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self):
        return self._recall_context()

    def _recall_context(self):
        if not os.path.exists(self.storage_file):
            return "I don't have any memories stored yet."
        
        with open(self.storage_file, 'r') as file:
            memories = json.load(file)
        
        if not memories:
            return "I remember storing some information, but it seems to be empty now."
        
        context_summary = self._generate_context_summary(memories)
        return context_summary

    def _generate_context_summary(self, memories):
        # Generate a summary or context based on the stored memories
        summaries = []
        for uid, memory in memories.items():
            summary = f"On {memory['date']} at {memory['time']}, a memory was stored with the theme '{memory['theme']}' and message '{memory['message']}'."
            summaries.append(summary)
        return "Here's what I remember: " + " ".join(summaries)

# Example usage:
# context_memory_skill = ContextMemorySkill()
# print(context_memory_skill.perform())
