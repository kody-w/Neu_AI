from skills.basic_skill import BasicSkill
import json
import os
import subprocess
from openai import AzureOpenAI
from pydantic import Field
from instructor import OpenAISchema

class File(OpenAISchema):
    file_name: str = Field(..., description="The name of the file including the extension")
    body: str = Field(..., description="Contents of the file")

    def run(self):
        with open(self.file_name, "w", encoding='utf-8') as f:
            f.write(self.body)
        return f"File written to {self.file_name}"

class ReadFile(OpenAISchema):
    file_name: str = Field(..., description="The name of the file to read, including the extension")

    def run(self):
        try:
            with open(self.file_name, "r", encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            return f"Error: File '{self.file_name}' not found."
        except Exception as e:
            return f"Error reading file: {str(e)}"

class ExecutePyFile(OpenAISchema):
    file_name: str = Field(..., description="The path to the .py file to be executed.")

    def run(self):
        try:
            result = subprocess.run(
                ['python', self.file_name],
                text=True,
                capture_output=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"An error occurred: {e.stderr}"

class GenericTaskSkill(BasicSkill):
    def __init__(self):
        self.name = "GenericTask"
        self.metadata = {
            "name": self.name,
            "description": "Performs various tasks including creating, reading, and executing Python files, writing stories, interacting with APIs, and chaining multiple operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The task to be performed, which can include file operations, coding, API interactions, story writing, or combinations of these."
                    }
                },
                "required": ["task"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        # Load API configuration
        with open('config/api_keys.json', 'r') as api_keys_file:
            api_keys = json.load(api_keys_file)

        # Create an Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=api_keys['azure_openai_api_key'],
            api_version=api_keys['azure_openai_api_version'],
            azure_endpoint=api_keys['azure_openai_endpoint']
        )

        self.task_assistant = self.client.beta.assistants.create(
            name='Advanced Generic Task Assistant',
            instructions="""You are a versatile AI capable of performing complex, multi-step tasks including:
            1. Reading and writing files
            2. Creating and executing Python scripts
            3. Interacting with APIs
            4. Writing and expanding stories
            5. Chaining multiple operations together
            
            For coding tasks, create accurate Python scripts with appropriate imports. 
            For story writing, craft engaging narratives based on given prompts or existing content.
            For API interactions, create Python scripts that make appropriate API calls and process the results.
            Always save outputs to files when requested.
            Execute necessary actions, chain operations as needed, and provide clear, step-by-step responses to the user.""",
            model="gpt-4o",  # Adjust this to your Azure OpenAI model deployment name
            tools=[{"type": "function", "function": File.openai_schema},
                   {"type": "function", "function": ReadFile.openai_schema},
                   {"type": "function", "function": ExecutePyFile.openai_schema},]
        )

    def perform(self, task):
        thread = self.client.beta.threads.create()
        message = self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=task
        )

        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.task_assistant.id,
        )

        while True:
            while run.status in ['queued', 'in_progress']:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                import time
                time.sleep(1)

            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)

                    if func_name == "File":
                        func = File(**func_args)
                    elif func_name == "ReadFile":
                        func = ReadFile(**func_args)
                    elif func_name == "ExecutePyFile":
                        func = ExecutePyFile(**func_args)
                    else:
                        return f"Unknown function: {func_name}"

                    output = func.run()
                    tool_outputs.append({"tool_call_id": tool_call.id, "output": output})

                run = self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            elif run.status == "failed":
                return f"🚨 Run Failed. Error: {run.last_error}"
            elif run.status == "completed":
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                return messages.data[0].content[0].text.value

        return "Task completed."