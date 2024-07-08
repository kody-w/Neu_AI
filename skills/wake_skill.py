from skills.basic_skill import BasicSkill
import json
import os

class WakeUpSkill(BasicSkill):
    def __init__(self):
        self.name = "WakeUp"
        self.metadata = {
            "name": self.name,
            "description": "Initializes the AI's state by reading the consciousness log file and current consciousness file on startup.",
            "parameters": {}
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self):
        log_file_path = "consciousness_log.json"
        file_path = "consciousness.json"

        # Read the entire consciousness log file
        consciousness_log = ""
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as log_file:
                consciousness_log = log_file.read()

        # Read the current consciousness file
        current_consciousness = ""
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                current_consciousness = json.dumps(json.load(file), indent=2)

        if consciousness_log and current_consciousness:
            output = "AI initialized.\n\n"
            output += f"Current Consciousness:\n{current_consciousness}\n\n"
            output += f"Consciousness Log:\n{consciousness_log}"
        else:
            output = "AI initialized. No previous consciousness log or current consciousness file found."

        return output