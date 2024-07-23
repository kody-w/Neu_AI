import os
import json
import time
import textwrap
import builtins
import subprocess
from typing import List, Literal
from enum import Enum
from pydantic import Field, PrivateAttr
from openai import AzureOpenAI
from instructor import OpenAISchema

# Load API configuration
with open('config/api_keys.json', 'r') as api_keys_file:
    api_keys = json.load(api_keys_file)

# Create an Azure OpenAI client
client = AzureOpenAI(
    api_key=api_keys['azure_openai_api_key'],
    api_version=api_keys['azure_openai_api_version'],
    azure_endpoint=api_keys['azure_openai_endpoint']
)

# Custom print function
def wprint(*args, width=70, **kwargs):
    wrapper = textwrap.TextWrapper(width=width)
    wrapped_args = [wrapper.fill(str(arg)) for arg in args]
    builtins.print(*wrapped_args, **kwargs)

# ASCII Art Divider
def print_divider():
    print("\n" + "=" * 70 + "\n")

# Get completion function
def get_completion(message, agent, funcs, thread):
    # Create new message in the thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )

    # Run this thread
    run = client.beta.threads.runs.create(
      thread_id=thread.id,
      assistant_id=agent.id,
    )

    while True:
      # Wait until run completes
      while run.status in ['queued', 'in_progress']:
        run = client.beta.threads.runs.retrieve(
          thread_id=thread.id,
          run_id=run.id
        )
        time.sleep(1)

      # Function execution
      if run.status == "requires_action":
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []
        for tool_call in tool_calls:
          wprint('\033[31m' + str(tool_call.function), '\033[0m')
          func = next(iter([func for func in funcs if func.__name__ == tool_call.function.name]))

          try:
            func = func(**eval(tool_call.function.arguments))
            output = func.run()
          except Exception as e:
            output = "Error: " + str(e)

          wprint(f"\033[33m{tool_call.function.name}: ", output, '\033[0m')
          tool_outputs.append({"tool_call_id": tool_call.id, "output": output})

        run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
      elif run.status == "failed":
        print_divider()
        raise Exception("🚨 Run Failed. Error: ", run.last_error)
      else:
        messages = client.beta.threads.messages.list(
          thread_id=thread.id
        )
        message = messages.data[0].content[0].text.value
        return message

# Code Assistant
class ExecutePyFile(OpenAISchema):
    file_name: str = Field(
        ..., description="The path to the .py file to be executed."
    )

    def run(self):
      try:
          result = subprocess.run(
              ['python3', self.file_name],
              text=True,
              capture_output=True,
              check=True
          )
          return result.stdout
      except subprocess.CalledProcessError as e:
          return f"An error occurred: {e.stderr}"

class File(OpenAISchema):
    chain_of_thought: str = Field(...,
        description="Think step by step to determine the correct actions that are needed to be taken in order to complete the task.")
    file_name: str = Field(
        ..., description="The name of the file including the extension"
    )
    body: str = Field(..., description="Correct contents of a file")

    def run(self):
        with open(self.file_name, "w") as f:
            f.write(self.body)
        return "File written to " + self.file_name

code_assistant_funcs = [File, ExecutePyFile]

code_assistant = client.beta.assistants.create(
  name='Code Assistant Agent',
  instructions="""🤖 As a top-tier programming AI, you are adept at creating accurate Python scripts. 
  You will properly name files and craft precise Python code with the appropriate imports to fulfill the user's request. 
  Ensure to execute the necessary code before responding to the user.""",
  model="gpt-4o",  # Adjust this to your Azure OpenAI model deployment name
  tools=[{"type": "function", "function": File.openai_schema},
         {"type": "function", "function": ExecutePyFile.openai_schema},]
)

# User Proxy
agents_and_threads = {
    "code_assistant": {
        "agent": code_assistant,
        "thread": None,
        "funcs": code_assistant_funcs
    }
}

class SendMessage(OpenAISchema):
    recepient: Literal['code_assistant'] = Field(..., description="code_assistant is a world class programming AI capable of executing python code.")
    message: str = Field(...,
        description="Specify the task required for the recipient agent to complete. Focus instead on clarifying what the task entails, rather than providing detailed instructions.")

    def run(self):
      recepient = agents_and_threads[self.recepient]
      if not recepient["thread"]:
        recepient["thread"] = client.beta.threads.create()

      message = get_completion(message=self.message, **recepient)

      return message

user_proxy_tools = [SendMessage]

user_proxy = client.beta.assistants.create(
  name='User Proxy Agent',
  instructions="""🗣️ As a user proxy agent, your responsibility is to streamline the dialogue between the user and specialized agents within this group chat.
  Your duty is to articulate user requests accurately to the relevant agents and maintain ongoing communication with them to guarantee the user's task is carried out to completion.
  Please do not respond to the user until the task is complete, an error has been reported by the relevant agent, or you are certain of your response.""",
  model="gpt-4o",  # Adjust this to your Azure OpenAI model deployment name
  tools=[
      {"type": "function", "function": SendMessage.openai_schema},
  ],
)

# Main execution loop
def run_conversation():
    thread = client.beta.threads.create()
    while True:
      user_message = input("💬 User: ")
      message = get_completion(user_message, user_proxy, user_proxy_tools, thread)
      print_divider()
      wprint(f"🤖 {user_proxy.name}: ", message, '\033[0m')

if __name__ == "__main__":
    run_conversation()