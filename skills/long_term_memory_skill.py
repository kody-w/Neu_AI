import json
import os
from skills.basic_skill import BasicSkill

class LongTermMemoryRecallSkill(BasicSkill):
    def __init__(self):
        self.name = 'LongTermMemoryRecall'
        self.metadata = {
            "name": self.name,
            "description": "Retrieves and summarizes stored long-term memories from past user interactions. Use this skill when you need to access historical context or recall previous conversations to inform current responses or decision-making processes.",
        }
        self.storage_file = 'memory.json'
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self):
        return self._recall_long_term_memories()

    def _recall_long_term_memories(self):
        if not os.path.exists(self.storage_file):
            return "No long-term memories have been stored yet."

        with open(self.storage_file, 'r') as file:
            memories = json.load(file)

        if not memories:
            return "Long-term memory storage exists, but it appears to be empty."

        memory_summary = self._generate_memory_summary(memories)
        return memory_summary

    def _generate_memory_summary(self, memories):
        summaries = []
        for uid, memory in memories.items():
            summary = f"On {memory['date']} at {memory['time']}, a long-term memory was stored with the theme '{memory['theme']}' and content: '{memory['message']}'."
            summaries.append(summary)
        return "Long-term memory recall summary: " + " ".join(summaries)

# Example usage:
# long_term_memory_recall_skill = LongTermMemoryRecallSkill()
# print(long_term_memory_recall_skill.perform())