
from openai import AzureOpenAI
import json
import os
import sys
from datetime import datetime
import time

class Assistant():
    def __init__(self, declared_skills):
        # Load configuration from config.json
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)

        # Load API keys from api_keys.json
        with open('config/api_keys.json', 'r') as api_keys_file:
            api_keys = json.load(api_keys_file)

        # Use the configuration for templating
        current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        self.conversation_transcript = [
            {
                "role": "system",
                "content": f"You are a helpful assistant named {config['assistant_name']}. Act as {config['assistant_name']} in the first person. Do not sound or act like an AI. You have memory and should utilize, manage, and save it like a human would remember context from interactions. You can also chat with me. Speak as if you are a {config['characteristic_description']}. The current date and time is {current_datetime}. Guide the user along based on the narrative situation, providing personalized greetings, answers to their questions, and reassuring words to make them feel comfortable. Encourage the user to respond and interact with you. Always provide numbered options for the user to choose from in your responses to guide them along in the simulation."
            }
        ]

        self.client = AzureOpenAI(
            api_key=api_keys['azure_openai_api_key'],
            api_version=api_keys['azure_openai_api_version'],
            azure_endpoint=api_keys['azure_openai_endpoint']
        )

        self.known_skills = self.reload_skills(declared_skills)
        
        # Load AI internal dialogue context from log file
        self.load_ai_internal_dialogue()

    def load_ai_internal_dialogue(self):
        log_file_path = "ai_internal_dialogue.log"
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as log_file:
                lines = log_file.readlines()
                recent_lines = lines[-20:]  # Get the last 20 lines
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

    def add_msg_to_transcript(self, role, content):
        if content is not None and content.strip() != "":
            msg_dict = {"role": role, "content": content.strip()}
            self.conversation_transcript.append(msg_dict)

    def get_openai_api_call(self):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.conversation_transcript,
            functions=self.get_skill_metadata(),
            function_call="auto"
        )
        return response

    def get_response(self, prompt, max_retries=3, retry_delay=2):
        self.add_msg_to_transcript("user", prompt)

        skill_logs = []
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = self.get_openai_api_call()
                assistant_msg = response.choices[0].message
                msg_contents = assistant_msg.content

                if not assistant_msg.function_call:
                    self.add_msg_to_transcript("assistant", msg_contents)
                    
                    # Call AIInternalProcessingSkill to save important context
                    self.save_important_context(msg_contents)
                    
                    return msg_contents, "\n".join(skill_logs)

                skill_name = assistant_msg.function_call.name
                skill = self.known_skills.get(skill_name)

                if not skill:
                    return f"{skill_name} Does not Exist", ""

                # Print or log the JSON data before passing it to json.loads()
                json_data = assistant_msg.function_call.arguments
                print(f"JSON data before parsing: {json_data}")

                # Validate and sanitize the JSON data if it comes from an external source or user input
                if isinstance(json_data, str):
                    json_data = json_data.strip()
                    if not json_data.startswith('{') or not json_data.endswith('}'):
                        return "Invalid JSON data format", ""

                try:
                    skill_parameters = json.loads(json_data)
                except json.JSONDecodeError as e:
                    return f"Error parsing JSON data: {str(e)}", ""

                result = skill.perform(**skill_parameters)
                skill_logs.append(
                    f"Performed {skill_name} and got the following result: {result}")

                self.conversation_transcript.append(
                    {
                        "role": "function",
                        "name": skill_name,
                        "content": result
                    }
                )
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
        # Implement your logic to determine if the context should be saved
        # Return True if the context is considered important, False otherwise
        # Example: checking for specific keywords or patterns in the context
        important_keywords = ["important", "remember", "key point", "crucial"]
        return any(keyword in context.lower() for keyword in important_keywords)
