import os
import json
import shutil
import subprocess
from skills.basic_skill import BasicSkill


class AssistantCreationSkill(BasicSkill):
    def __init__(self):
        self.name = 'AssistantCreation'
        self.metadata = {
            'name': self.name,
            'description': 'A skill to create an assistant based on a assistant name and required characteristics.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'assistant_name': {
                        'type': 'string',
                        'description': 'The name of the assistant'
                    },
                    'characteristic_description': {
                        'type': 'string',
                        'description': 'A detailed description of the characteristics that the assistant will involve, including the expected inputs, outputs, and any specific requirements or constraints.'
                    }
                },
                'required': ['assistant_name', 'characteristic_description']
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, assistant_name, characteristic_description):
        # Create a directory for the created assistants
        created_assistants_dir = "created_assistants"
        os.makedirs(created_assistants_dir, exist_ok=True)

        # Create a unique directory for the assistant
        assistant_dir = os.path.join(
            created_assistants_dir, assistant_name.lower().replace(' ', '_'))
        os.makedirs(assistant_dir, exist_ok=True)

        # Create a skills directory for the assistant
        assistant_skills_dir = os.path.join(assistant_dir, "skills")
        os.makedirs(assistant_skills_dir, exist_ok=True)

        # Create a config directory for the assistant
        assistant_config_dir = os.path.join(assistant_dir, "config")
        os.makedirs(assistant_config_dir, exist_ok=True)

        # Copy the necessary skill files to the assistant's skills directory
        # Add your actual skill file names here
        skill_files = ["basic_skill.py",
                       "manage_memory_skill.py", "context_memory_skill.py"]
        for skill_file in skill_files:
            src_path = os.path.join("skills", skill_file)
            dst_path = os.path.join(assistant_skills_dir, skill_file)
            shutil.copy(src_path, dst_path)

        # Copy the api_keys.json file to the assistant's config directory
        api_keys_src = os.path.join("config", "api_keys.json")
        api_keys_dst = os.path.join(assistant_config_dir, "api_keys.json")
        if os.path.exists(api_keys_src):
            shutil.copy(api_keys_src, api_keys_dst)
        else:
            print(
                f"Warning: api_keys.json not found at {api_keys_src}. You may need to create this file manually.")

        # Save the configuration to a unique file in the assistant's directory
        config_file = os.path.join(assistant_dir, "config.json")
        config = {
            'assistant_name': assistant_name,
            'characteristic_description': characteristic_description
        }
        with open(config_file, 'w') as file:
            json.dump(config, file)

        # Generate the assistant code based on the provided template
        assistant_code = '''
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
                "content": f"The following is a log of your most recent interactions with the user, which you can leverage in the current conversation if relevant. These interactions provide context about the user's interests, preferences, and previous discussions. Use this information to personalize your responses and maintain continuity in the conversation.\\n\\nAI Internal Dialogue Context:\\n{ai_internal_dialogue}"
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
                    
                    return msg_contents, "\\n".join(skill_logs)

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
'''

        # Generate the interface code for the assistant
        interface_code = '''
import json
import sys
import os
import importlib
import inspect
import re
from termcolor import colored, cprint
from assistant import Assistant
from skills.basic_skill import BasicSkill

def load_skills_from_folder():
    files_in_skills_directory = os.listdir("./skills")
    skill_files = []
    for file in files_in_skills_directory:
        if not file.endswith(".py"):
            continue
        forbidden_files = ["__init__.py", "basic_skill.py"]
        if file in forbidden_files:
            continue
        skill_files.append(file)

    skill_module_names = []
    for file in skill_files:
        skill_module_names.append(file[:-3])

    declared_skills = []
    for skill in skill_module_names:
        module = importlib.import_module('skills.' + skill)
        for name, member in inspect.getmembers(module):
            if not (inspect.isclass(member) and issubclass(member, BasicSkill)):
                continue
            if member is BasicSkill:
                continue
            declared_skills.append(member())

    return declared_skills

def filter_text(text):
    # Remove any characters that are not alphanumeric, space, or punctuation
    filtered_text = re.sub(r'[^a-zA-Z0-9\\s\\.,!?]', '', text)
    return filtered_text

def speak(response, assistant_name):
    text, additional_output = response
    
    filtered_text = filter_text(text)
    cprint(assistant_name + f":🌐📞 {text}", 'cyan')
    
    if additional_output:
        print(additional_output)

if __name__ == "__main__":
    declared_skills = load_skills_from_folder()

    # Load configuration from config.json
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    assistant_name = config['assistant_name']
    assistant = Assistant(declared_skills)
    cprint(f"Welcome to {assistant_name}, your command line assistant!", 'yellow', 'on_red', attrs=['bold', 'blink'])
    cprint("Type 'help' for a list of commands or 'exit' to quit.", 'yellow')

    while True:
        user_input = input(colored("User>😎📞", 'green'))
        if user_input.lower() == 'exit':
            cprint(f"Goodbye from {assistant_name}! 👋", 'yellow')
            break
        else:
            user_sentence = user_input
        
        assistant_response = assistant.get_response(user_sentence)
        speak(assistant_response, assistant_name)
'''

        # Save the assistant code to a file in the assistant's directory
        assistant_file_path = os.path.join(assistant_dir, "assistant.py")
        with open(assistant_file_path, 'w', encoding='utf-8') as file:
            file.write(assistant_code)

        # Save the interface code to a file in the assistant's directory
        interface_file_path = os.path.join(assistant_dir, "interface.py")
        with open(interface_file_path, 'w', encoding='utf-8') as file:
            file.write(interface_code)

        return f"The {assistant_name} assistant has been created successfully in the '{assistant_dir}' directory."

    def interact_with_assistant(self, assistant_name, task):
        assistant_dir = os.path.join(
            "created_assistants", assistant_name.lower().replace(' ', '_'))
        interface_file_path = os.path.join(assistant_dir, "interface.py")

        num_attempts = 3
        for attempt in range(1, num_attempts + 1):
            print(f"\nInteraction Attempt {attempt}/{num_attempts}")

            # Call the created assistant's interface with the task as input
            process = subprocess.Popen(["python", interface_file_path], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output, _ = process.communicate(input=task)

            # Extract the assistant's response from the output
            assistant_response = self.extract_assistant_response(output)

            print(f"Created Assistant's Response:\n{assistant_response}")

            # Ask the super assistant if the response is satisfactory
            satisfactory = input(
                "Is the created assistant's response satisfactory? (yes/no): ")
            if satisfactory.lower() == "yes":
                return assistant_response

        return "The created assistant could not provide a satisfactory response after 3 attempts."

    def extract_assistant_response(self, output):
        # Extract the assistant's response from the output
        # You can customize this method based on the format of the output
        # For simplicity, let's assume the assistant's response is the last line of the output
        lines = output.strip().split("\n")
        return lines[-1]

    def list_created_assistants(self):
        created_assistants_dir = "created_assistants"
        if not os.path.exists(created_assistants_dir):
            return "No assistants have been created yet."

        assistants = os.listdir(created_assistants_dir)
        if not assistants:
            return "No assistants have been created yet."

        return "Created Assistants:\n" + "\n".join(assistants)

    def delete_assistant(self, assistant_name):
        assistant_dir = os.path.join(
            "created_assistants", assistant_name.lower().replace(' ', '_'))
        if not os.path.exists(assistant_dir):
            return f"Assistant '{assistant_name}' not found."

        try:
            shutil.rmtree(assistant_dir)
            return f"Assistant '{assistant_name}' has been deleted successfully."
        except Exception as e:
            return f"An error occurred while deleting the assistant: {str(e)}"

    def update_assistant(self, assistant_name, new_characteristic_description):
        assistant_dir = os.path.join(
            "created_assistants", assistant_name.lower().replace(' ', '_'))
        if not os.path.exists(assistant_dir):
            return f"Assistant '{assistant_name}' not found."

        config_file = os.path.join(assistant_dir, "config.json")
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)

            config['characteristic_description'] = new_characteristic_description

            with open(config_file, 'w') as file:
                json.dump(config, file, indent=2)

            return f"Assistant '{assistant_name}' has been updated successfully."
        except Exception as e:
            return f"An error occurred while updating the assistant: {str(e)}"

    def get_assistant_info(self, assistant_name):
        assistant_dir = os.path.join(
            "created_assistants", assistant_name.lower().replace(' ', '_'))
        if not os.path.exists(assistant_dir):
            return f"Assistant '{assistant_name}' not found."

        config_file = os.path.join(assistant_dir, "config.json")
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)

            return f"Assistant Name: {config['assistant_name']}\nCharacteristics: {config['characteristic_description']}"
        except Exception as e:
            return f"An error occurred while retrieving assistant information: {str(e)}"

    def backup_assistant(self, assistant_name, backup_dir="assistant_backups"):
        source_dir = os.path.join(
            "created_assistants", assistant_name.lower().replace(' ', '_'))
        if not os.path.exists(source_dir):
            return f"Assistant '{assistant_name}' not found."

        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(
            backup_dir, f"{assistant_name.lower().replace(' ', '_')}_backup")

        try:
            shutil.copytree(source_dir, backup_path)
            return f"Assistant '{assistant_name}' has been backed up successfully to {backup_path}."
        except Exception as e:
            return f"An error occurred while backing up the assistant: {str(e)}"

    def restore_assistant(self, assistant_name, backup_dir="assistant_backups"):
        backup_path = os.path.join(
            backup_dir, f"{assistant_name.lower().replace(' ', '_')}_backup")
        if not os.path.exists(backup_path):
            return f"Backup for assistant '{assistant_name}' not found."

        target_dir = os.path.join(
            "created_assistants", assistant_name.lower().replace(' ', '_'))

        try:
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            shutil.copytree(backup_path, target_dir)
            return f"Assistant '{assistant_name}' has been restored successfully from backup."
        except Exception as e:
            return f"An error occurred while restoring the assistant: {str(e)}"

# End of AssistantCreationSkill class
