import asyncio
from skills.basic_skill import BasicSkill
from assistant import Assistant
import json

class AsyncAssistantSkill(BasicSkill):
    def __init__(self):
        self.name = "AsyncAssistant"
        self.metadata = {
            "name": self.name,
            "description": "Creates and interacts with a sub-assistant asynchronously, driven by the main assistant's instructions. This skill allows for complex, multi-turn interactions where the main assistant can guide a sub-assistant through a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "initial_task": {
                        "type": "string",
                        "description": "The initial task or question for the sub-assistant. This should be a clear, detailed instruction that sets up the context for the entire interaction. For example, 'Write a Python function to calculate the Fibonacci sequence up to n terms.' The more specific and well-defined this task is, the better the sub-assistant can perform."
                    },
                    "max_turns": {
                        "type": "integer",
                        "description": "The maximum number of back-and-forth interactions between the main assistant and the sub-assistant. Each 'turn' consists of the sub-assistant's response followed by the main assistant's evaluation and next instruction. This should be set based on the complexity of the task. For simple tasks, 3-5 turns might be sufficient, while more complex tasks might require 10-20 turns. The interaction will stop either when this number is reached or when the main assistant determines the task is complete."
                    }
                },
                "required": ["initial_task", "max_turns"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        # Load configuration
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

    async def create_assistant(self):
        # Create a new Assistant instance
        new_assistant = Assistant(["basic_skill.py"])  # Pass an empty list of skills for this sub-assistant
        return new_assistant

    async def send_message(self, assistant, message):
        response, _ = assistant.get_response(message)
        return response

    async def interact_with_assistant(self, main_assistant, sub_assistant, initial_task, max_turns):
        conversation = [f"Initial Task: {initial_task}"]
        for turn in range(max_turns):
            # Sub-assistant responds
            sub_response = await self.send_message(sub_assistant, "\n".join(conversation))
            conversation.append(f"Sub-Assistant: {sub_response}")
            yield f"Turn {turn + 1} - Sub-Assistant: {sub_response}"
            
            # Main assistant evaluates and provides next instruction
            main_prompt = f"""
            You are overseeing a conversation with a sub-assistant. Here's the conversation so far:
            
            {conversation}
            
            Based on this, provide the next instruction or question for the sub-assistant. 
            If the task seems complete or if you have no further instructions, respond with 'TASK_COMPLETE'.
            Your response:
            """
            main_response, _ = main_assistant.get_response(main_prompt)
            
            if main_response.strip().upper() == 'TASK_COMPLETE':
                yield f"Turn {turn + 1} - Main Assistant: Task complete. Ending interaction."
                break
            
            conversation.append(f"Main Assistant: {main_response}")
            yield f"Turn {turn + 1} - Main Assistant: {main_response}"

    async def run_async_interaction(self, main_assistant, initial_task, max_turns):
        sub_assistant = await self.create_assistant()
        async for response in self.interact_with_assistant(main_assistant, sub_assistant, initial_task, max_turns):
            yield response

    def perform(self, initial_task, max_turns):
        async def run():
            responses = []
            main_assistant = self  # 'self' here refers to the main Assistant instance
            async for response in self.run_async_interaction(main_assistant, initial_task, max_turns):
                responses.append(response)
            return responses

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(run())