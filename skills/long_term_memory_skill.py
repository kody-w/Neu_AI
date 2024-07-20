import json
import os
from skills.basic_skill import BasicSkill

class LongTermMemorySkill(BasicSkill):
    def __init__(self):
        self.name = 'LongTermMemory'
        self.metadata = {
            "name": self.name,
            "description": "Accesses and retrieves long-term memories and past events from interactions with the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional query to filter memories (e.g., 'business', 'personal', date range)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Optional limit on the number of memories to return"
                    }
                }
            }
        }
        self.storage_file = 'memory.json'
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, query=None, limit=10):
        return self._access_long_term_memory(query, limit)

    def _access_long_term_memory(self, query=None, limit=10):
        if not os.path.exists(self.storage_file):
            return "I don't have any long-term memories stored yet."
        
        with open(self.storage_file, 'r') as file:
            memories = json.load(file)
        
        if not memories:
            return "I remember storing some long-term information, but it seems to be empty now."
        
        filtered_memories = self._filter_memories(memories, query)
        memory_summary = self._generate_memory_summary(filtered_memories, limit)
        return memory_summary

    def _filter_memories(self, memories, query):
        if not query:
            return memories
        
        filtered = {}
        for uid, memory in memories.items():
            if (query.lower() in memory.get('theme', '').lower() or 
                query.lower() in memory.get('message', '').lower() or
                query.lower() in memory.get('date', '')):
                filtered[uid] = memory
        return filtered

    def _generate_memory_summary(self, memories, limit):
        if not memories:
            return "I couldn't find any relevant long-term memories based on the query."
        
        # Sort memories by date and time strings
        sorted_memories = sorted(memories.items(), key=lambda x: (x[1].get('date', ''), x[1].get('time', '')), reverse=True)
        
        summaries = []
        for uid, memory in sorted_memories[:limit]:
            summary = (f"On {memory.get('date', 'unknown date')} at {memory.get('time', 'unknown time')}, "
                       f"I stored a memory with the theme '{memory.get('theme', 'Unspecified')}': {memory.get('message', 'No message')}")
            summaries.append(summary)
        
        return "Here are the relevant memories I've accessed:\n\n" + "\n\n".join(summaries)

# Example usage:
# long_term_memory_skill = LongTermMemorySkill()
# print(long_term_memory_skill.perform(query="business", limit=5))