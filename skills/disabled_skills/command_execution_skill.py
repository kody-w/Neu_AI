from skills.basic_skill import BasicSkill
import json
from datetime import datetime
import subprocess
import shlex
import os
import platform

class CommandExecutionSkill(BasicSkill):
    def __init__(self):
        self.name = "CommandExecution"
        self.metadata = {
            "name": self.name,
            "description": "Executes commands and maintains a command pipeline with cross-platform support.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "execute", "get_pipeline", "clear_pipeline"],
                        "description": "The action to perform on the command pipeline."
                    },
                    "command": {
                        "type": "string",
                        "description": "The command to add or execute (for 'add' and 'execute' actions)."
                    },
                    "arguments": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Arguments for the command (for 'add' and 'execute' actions)."
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.pipeline_file = "command_pipeline.json"
        self.load_pipeline()
        self.is_windows = platform.system().lower() == "windows"

    def load_pipeline(self):
        try:
            with open(self.pipeline_file, 'r') as file:
                self.pipeline = json.load(file)
        except FileNotFoundError:
            self.pipeline = []
        self.save_pipeline()

    def save_pipeline(self):
        with open(self.pipeline_file, 'w') as file:
            json.dump(self.pipeline, file, indent=2)

    def perform(self, action, command=None, arguments=None):
        if action == "add":
            return self.add_command(command, arguments)
        elif action == "execute":
            return self.execute_command(command, arguments)
        elif action == "get_pipeline":
            return self.get_pipeline()
        elif action == "clear_pipeline":
            return self.clear_pipeline()
        else:
            return "Invalid action. Use 'add', 'execute', 'get_pipeline', or 'clear_pipeline'."

    def add_command(self, command, arguments=None):
        if not command:
            return "Please provide a command to add to the pipeline."
        
        self.pipeline.append({
            "command": command,
            "arguments": arguments or [],
            "added_at": datetime.now().isoformat()
        })
        self.save_pipeline()
        return f"Command '{command}' added to the pipeline."

    def execute_command(self, command=None, arguments=None):
        if command:
            return self._run_command(command, arguments)
        elif self.pipeline:
            results = []
            for cmd in self.pipeline:
                result = self._run_command(cmd["command"], cmd["arguments"])
                results.append(result)
            self.clear_pipeline()
            return "\n".join(results)
        else:
            return "No commands in the pipeline to execute."

    def _run_command(self, command, arguments=None):
        # Use a whitelist of allowed commands for security
        allowed_commands = {
            "windows": ["echo", "dir", "type", "systeminfo"],
            "unix": ["echo", "ls", "cat", "uname"]
        }
        
        if self.is_windows:
            if command not in allowed_commands["windows"]:
                return f"Command '{command}' is not allowed on Windows for security reasons."
            if command == "ls":
                command = "dir"  # Map 'ls' to 'dir' on Windows
        else:
            if command not in allowed_commands["unix"]:
                return f"Command '{command}' is not allowed on Unix-like systems for security reasons."
        
        full_command = [command] + (arguments or [])
        try:
            # Use shell=True for Windows to handle built-in commands
            result = subprocess.run(full_command, capture_output=True, text=True, shell=self.is_windows)
            return f"Command: {' '.join(full_command)}\nOutput: {result.stdout}\nErrors: {result.stderr}"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def get_pipeline(self):
        if not self.pipeline:
            return "The command pipeline is empty."
        return json.dumps(self.pipeline, indent=2)

    def clear_pipeline(self):
        self.pipeline = []
        self.save_pipeline()
        return "Command pipeline cleared."