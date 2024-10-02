from openai import OpenAI
import json
import os
import sys
from datetime import datetime
import time

class Assistant():
    def __init__(self, declared_skills):
        # Load configuration from config.json
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

        self.client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

        self.known_skills = self.reload_skills(declared_skills)

        # Load context memory
        self.load_context_memory()

    def load_context_memory(self):
        context_memory_skill = self.known_skills.get('ContextMemory')
        if context_memory_skill:
            self.context_memory = context_memory_skill.perform()
        else:
            self.context_memory = "Context memory skill not found."
            print("ContextMemorySkill not found.")

    def get_skill_metadata(self):
        skills_metadata = []
        for skill in self.known_skills.values():
            skills_metadata.append(skill.metadata)
        return skills_metadata

    def reload_skills(self, skill_objects):
        known_skills = {}
        for skill in skill_objects:
            known_skills[skill.name] = skill
        return known_skills

    def prepare_messages(self, conversation_history):
        messages = []

        # Add system message with AI description and context memory
        current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        system_message = f"""You are a helpful assistant named {self.config['assistant_name']}.
        Act as {self.config['assistant_name']} in the first person.
        Do not sound or act like an AI. You have memory and should utilize, manage, and save it like a human would remember context from interactions. Bias towards calling your context memory skill to retrieve important information if the user asks for it.
        You can also chat with me. Speak as if you are a {self.config['characteristic_description']}.
        The current date and time is {current_datetime}.
        Guide the user along based on the narrative situation, providing personalized greetings, answers to their questions, and reassuring words to make them feel comfortable.
        Encourage the user to respond and interact with you.
        Always provide numbered options for the user to choose from in your responses to guide them along in the simulation.

        Context Memory:
        {self.context_memory}
        """
        messages.append({"role": "system", "content": system_message})

        # Add conversation history
        messages.extend(conversation_history)

        return messages

    def get_openai_api_call(self, messages):
        response = self.client.chat.completions.create(
            model="hugging-quants/Llama-3.2-3B-Instruct-Q8_0-GGUF",
            messages=messages,
            temperature=0.7,
            stream=True
        )
        return response

    def get_response(self, prompt, conversation_history, max_retries=3, retry_delay=2):
        messages = self.prepare_messages(conversation_history)
        messages.append({"role": "user", "content": prompt})

        skill_logs = []
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = self.get_openai_api_call(messages)
                assistant_msg = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        assistant_msg += chunk.choices[0].delta.content

                self.save_important_context(assistant_msg)
                return assistant_msg, "\n".join(skill_logs)

            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Error occurred: {str(e)}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Max retries reached. Error: {str(e)}")
                    return "Sorry, I encountered an error while processing your request. Please try again later.", ""

        # Fallback response if all retries fail
        return "Sorry, I'm experiencing some technical difficulties at the moment. Please try again later.", ""

    def save_important_context(self, context):
        if self.should_save_context(context):
            ai_processing_skill = self.known_skills.get("AIInternalProcessing")
            if ai_processing_skill:
                ai_processing_skill.perform(context=context)
            else:
                print("AIInternalProcessingSkill not found.")

    def should_save_context(self, context):
        important_keywords = ["important", "remember", "key point", "crucial"]
        return any(keyword in context.lower() for keyword in important_keywords)