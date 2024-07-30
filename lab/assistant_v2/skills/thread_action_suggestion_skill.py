from skills.basic_skill import BasicSkill
import json

class ThreadActionSuggestionSkill(BasicSkill):
    def __init__(self):
        self.name = "ThreadActionSuggestion"
        self.metadata = {
            "name": self.name,
            "description": "Suggests the next best action for thread commands based on the current context of the chat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_thread_id": {
                        "type": "string",
                        "description": "The ID of the current thread, if any."
                    },
                    "recent_messages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        },
                        "description": "The most recent messages in the current thread."
                    },
                    "available_threads": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "created_at": {"type": "string"}
                            }
                        },
                        "description": "List of available threads in the library."
                    }
                },
                "required": ["current_thread_id", "recent_messages", "available_threads"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, current_thread_id, recent_messages, available_threads):
        suggestions = []

        # Suggest summarizing if the current thread has many messages
        if len(recent_messages) >= 10:
            suggestions.append("Use 'summary' to get an overview of the current conversation.")

        # Suggest branching if the conversation seems to be taking a new direction
        if len(recent_messages) >= 3:
            last_two_messages = recent_messages[-2:]
            if any(self.is_topic_shift(msg['content']) for msg in last_two_messages):
                suggestions.append("Consider using 'branch <message_id>' to explore this new direction in a separate thread.")

        # Suggest switching to another thread if there are other available threads
        other_threads = [thread for thread in available_threads if thread['id'] != current_thread_id]
        if other_threads:
            suggestions.append(f"You have {len(other_threads)} other thread(s). Use 'switch <thread_id>' to change to another conversation.")

        # Suggest listing threads if there are multiple threads
        if len(available_threads) > 1:
            suggestions.append("Use 'list threads' to see all your saved conversations.")

        # Suggest deleting old threads if there are many
        if len(available_threads) > 5:
            suggestions.append("You have many saved threads. Consider using 'delete thread <thread_id>' to remove old or unnecessary conversations.")

        if not suggestions:
            suggestions.append("Continue the current conversation or start a new topic.")

        return json.dumps(suggestions)

    def is_topic_shift(self, message):
        # This is a simple heuristic. In a real-world scenario, you might use more sophisticated NLP techniques.
        topic_shift_phrases = ["by the way", "on another note", "changing the subject", "speaking of which"]
        return any(phrase in message.lower() for phrase in topic_shift_phrases)