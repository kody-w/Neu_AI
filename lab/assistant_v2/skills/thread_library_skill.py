from skills.basic_skill import BasicSkill
import json
import os
from datetime import datetime

class ThreadLibrarySkill(BasicSkill):
    def __init__(self):
        self.name = "ThreadLibrary"
        self.metadata = {
            "name": self.name,
            "description": "Manages a library of chat threads stored locally in a JSON file, including detailed context and user information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["save", "update", "retrieve", "list", "delete", "log_interaction"],
                        "description": "The action to perform on the thread library."
                    },
                    "thread_id": {
                        "type": "string",
                        "description": "The ID of the thread to save, update, retrieve, or delete."
                    },
                    "thread_data": {
                        "type": "object",
                        "description": "The data of the thread to save or update."
                    },
                    "summary": {
                        "type": "string",
                        "description": "A brief summary of the thread's context."
                    },
                    "user_info": {
                        "type": "object",
                        "description": "Information about the current user."
                    },
                    "interaction_details": {
                        "type": "object",
                        "description": "Details about the current interaction."
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.library_file = "thread_library.json"
        self.initialize_library()

    def initialize_library(self):
        if not os.path.exists(self.library_file):
            with open(self.library_file, 'w') as f:
                json.dump({}, f)

    def load_library(self):
        with open(self.library_file, 'r') as f:
            return json.load(f)

    def save_library(self, library):
        with open(self.library_file, 'w') as f:
            json.dump(library, f, indent=2)

    def perform(self, action, thread_id=None, thread_data=None, summary=None, user_info=None, interaction_details=None):
        library = self.load_library()

        if action == "save":
            if thread_id is None or thread_data is None or summary is None or user_info is None:
                return "Error: thread_id, thread_data, summary, and user_info are required for save action."
            library[thread_id] = {
                "data": thread_data,
                "summary": summary,
                "user_info": user_info,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "interactions": []
            }
            self.save_library(library)
            return f"Thread {thread_id} saved successfully."

        elif action == "update":
            if thread_id is None or thread_data is None or summary is None:
                return "Error: thread_id, thread_data, and summary are required for update action."
            if thread_id not in library:
                return f"Error: Thread {thread_id} not found in the library."
            library[thread_id]["data"] = thread_data
            library[thread_id]["summary"] = summary
            library[thread_id]["updated_at"] = datetime.now().isoformat()
            self.save_library(library)
            return f"Thread {thread_id} updated successfully."

        elif action == "retrieve":
            if thread_id is None:
                return "Error: thread_id is required for retrieve action."
            if thread_id not in library:
                return f"Error: Thread {thread_id} not found in the library."
            return json.dumps(library[thread_id], indent=2)

        elif action == "list":
            return json.dumps([{
                "id": k,
                "summary": v["summary"],
                "user_info": v["user_info"],
                "created_at": v["created_at"],
                "updated_at": v["updated_at"],
                "interaction_count": len(v["interactions"])
            } for k, v in library.items()], indent=2)

        elif action == "delete":
            if thread_id is None:
                return "Error: thread_id is required for delete action."
            if thread_id not in library:
                return f"Error: Thread {thread_id} not found in the library."
            del library[thread_id]
            self.save_library(library)
            return f"Thread {thread_id} deleted successfully."

        elif action == "log_interaction":
            if thread_id is None or interaction_details is None:
                return "Error: thread_id and interaction_details are required for log_interaction action."
            if thread_id not in library:
                return f"Error: Thread {thread_id} not found in the library."
            library[thread_id]["interactions"].append({
                "timestamp": datetime.now().isoformat(),
                **interaction_details
            })
            library[thread_id]["updated_at"] = datetime.now().isoformat()
            self.save_library(library)
            return f"Interaction logged for thread {thread_id}."

        else:
            return f"Error: Unknown action '{action}'."