from openai import OpenAI
import json
import os
import sys
from datetime import datetime
import time

class Assistant():
    def __init__(self, declared_skills):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)

        current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        self.conversation_transcript = [
            {
                "role": "system",
                "content": f"You are a helpful assistant named {config['assistant_name']}. Act as {config['assistant_name']} in the first person. Do not sound or act like an AI. You have memory and should utilize, manage, and save it like a human would remember context from interactions. You can also chat with me. Speak as if you are a {config['characteristic_description']}. The current date and time is {current_datetime}. Guide the user along based on the narrative situation, providing personalized greetings, answers to their questions, and reassuring words to make them feel comfortable. Encourage the user to respond and interact with you. Always provide numbered options for the user to choose from in your responses to guide them along in the simulation."
            }
        ]

        self.client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

        self.known_skills = self.reload_skills(declared_skills)
        
        self.load_ai_internal_dialogue()

    def load_ai_internal_dialogue(self):
        log_file_path = "ai_internal_dialogue.log"
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as log_file:
                lines = log_file.readlines()
                recent_lines = lines[-20:]
                ai_internal_dialogue = "".join(recent_lines)
            self.conversation_transcript.append({
                "role": "system",
                "content": f"The following is a log of your most recent interactions with the user, which you can leverage in the current conversation if relevant. These interactions provide context about the user's interests, preferences, and previous discussions. Use this information to personalize your responses and maintain continuity in the conversation.\n\nAI Internal Dialogue Context:\n{ai_internal_dialogue}"
            })
        else:
            print(f"AI internal dialogue log file not found at {log_file_path}")

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

    def add_msg_to_transcript(self, role, content, name=None):
        if content is not None:
            if isinstance(content, (list, dict)):
                content = json.dumps(content)
            msg_dict = {"role": role, "content": content.strip() if isinstance(content, str) else content}
            if role == "function":
                msg_dict["name"] = name or "unknown_function"
            self.conversation_transcript.append(msg_dict)

    def get_openai_api_call(self):
        formatted_messages = []
        for message in self.conversation_transcript:
            if message["role"] == "function":
                formatted_message = {
                    "role": "function",
                    "name": message.get("name", "unknown_function"),
                    "content": message["content"]
                }
            else:
                formatted_message = {
                    "role": message["role"],
                    "content": message["content"]
                }
            formatted_messages.append(formatted_message)

        response = self.client.chat.completions.create(
            model="hugging-quants/Llama-3.2-3B-Instruct-Q8_0-GGUF",
            messages=formatted_messages,
            temperature=0.7,
            stream=True
        )
        return response

    def get_response(self, prompt, max_retries=3, retry_delay=2):
        self.add_msg_to_transcript("user", prompt)

        skill_logs = []
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = self.get_openai_api_call()
                assistant_msg = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        assistant_msg += chunk.choices[0].delta.content

                self.add_msg_to_transcript("assistant", assistant_msg)
                
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