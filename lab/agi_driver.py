import os
import json
import time
import textwrap
import builtins
from typing import List, Literal
from pydantic import Field
from openai import AzureOpenAI
from instructor import OpenAISchema
from assistantv2 import Assistant
from interfacev2 import load_skills_from_folder

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

# Assistant Interaction
class InteractWithAssistant(OpenAISchema):
    message: str = Field(...,
        description="The message to send to the Assistant.")

    def run(self):
        global assistant
        response, _ = assistant.get_response(self.message)
        return response

# User Proxy
user_proxy_tools = [InteractWithAssistant]

user_proxy = client.beta.assistants.create(
  name='User Proxy Agent',
  instructions="""🗣️ As a user proxy agent, your responsibility is to interact with the Assistant.
  Your duty is to articulate user requests accurately to the Assistant and maintain ongoing communication to guarantee the user's task is carried out to completion.
  Always use the InteractWithAssistant function to communicate with the Assistant, and relay the Assistant's responses back to the user.
  Do not try to answer the user's questions yourself; always defer to the Assistant's responses.""",
  model="gpt-4o",  # Adjust this to your Azure OpenAI model deployment name
  tools=[
      {"type": "function", "function": InteractWithAssistant.openai_schema},
  ],
)

# Initialize Assistant
declared_skills = load_skills_from_folder()
assistant = Assistant(declared_skills)

# Main execution loop
def run_conversation():
    thread = client.beta.threads.create()
    while True:
      user_message = input("💬 User: ")
      if user_message.lower() == 'exit':
          print("Goodbye!")
          break
      message = get_completion(user_message, user_proxy, user_proxy_tools, thread)
      print_divider()
      wprint(f"🤖 Assistant: ", message, '\033[0m')

if __name__ == "__main__":
    run_conversation()