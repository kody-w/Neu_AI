import os
import time
import json
from openai import AzureOpenAI
from datetime import datetime

class Assistant:
    def __init__(self, declared_skills):
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

        with open('config/api_keys.json', 'r') as api_keys_file:
            api_keys = json.load(api_keys_file)

        self.client = AzureOpenAI(
            api_key=api_keys['azure_openai_api_key'],
            api_version=api_keys['azure_openai_api_version'],
            azure_endpoint=api_keys['azure_openai_endpoint']
        )

        self.known_skills = {skill.name: skill for skill in declared_skills}
        self.assistant = self.create_assistant()
        self.thread = self.client.beta.threads.create()

    def create_assistant(self):
        tools = []
        for skill in self.known_skills.values():
            function_metadata = skill.metadata.get('parameters', {})
            tools.append({
                "type": "function",
                "function": {
                    "name": skill.name,
                    "description": skill.metadata.get('description', ''),
                    "parameters": function_metadata
                }
            })
        
        return self.client.beta.assistants.create(
            name=self.config['assistant_name'],
            instructions=f"You are {self.config['assistant_name']}, a helpful AI assistant. {self.config['characteristic_description']}",
            model=self.config.get('model', 'gpt-4o'),
            tools=tools
        )

    def get_response(self, user_input):
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=user_input
        )

        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id
        )

        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )

        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            assistant_message = next((msg for msg in messages.data if msg.role == "assistant"), None)
            return assistant_message.content[0].text.value, ""
        elif run.status == 'requires_action':
            return self.handle_function_calls(run)
        else:
            return f"An error occurred: {run.status}", ""

    def handle_function_calls(self, run):
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name in self.known_skills:
                skill = self.known_skills[function_name]
                result = skill.perform(**function_args)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                })
            else:
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"error": f"Unknown function: {function_name}"})
                })

        run = self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )

        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )

        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            assistant_message = next((msg for msg in messages.data if msg.role == "assistant"), None)
            return assistant_message.content[0].text.value, ""
        else:
            return f"An error occurred while processing function calls: {run.status}", ""

    def save_important_context(self, context):
        # Implementation for saving important context (if needed)
        pass