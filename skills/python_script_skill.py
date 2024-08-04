from skills.basic_skill import BasicSkill
import subprocess


class PythonScriptSkill(BasicSkill):
    def __init__(self):
        self.name = 'PythonScript'
        self.metadata = {
            "name": self.name,
            "description": "Runs a long running Python script and returns the output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script_path": {
                        "type": "string",
                        "description": "The file path of the Python script to execute."
                    },
                },
                "required": ["script_path"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, script_path):
        try:
            process = subprocess.Popen(
                ['python', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

            # Stream the output to the console
            for line in process.stdout:
                print(line, end='')

            # Wait for the process to finish and capture the error (if any)
            _, error = process.communicate()

            if process.returncode == 0:
                return "Script executed successfully."
            else:
                return f"Script execution failed. Error: {error}"
        except Exception as e:
            return f"An error occurred: {str(e)}"
