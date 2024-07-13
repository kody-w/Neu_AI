import os
import json
import shutil
import subprocess
from skills.basic_skill import BasicSkill
import autogen

class AutoGenGroupChatSkill(BasicSkill):
    def __init__(self):
        self.name = 'AutoGenGroupChat'
        self.metadata = {
            'name': self.name,
            'description': 'A skill to create and manage AutoGen-based group chats.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'chat_name': {
                        'type': 'string',
                        'description': 'The name of the group chat'
                    },
                    'task_description': {
                        'type': 'string',
                        'description': 'A detailed description of the task for the group chat'
                    },
                    'num_participants': {
                        'type': 'integer',
                        'description': 'The number of AI participants in the group chat'
                    },
                    'max_turns': {
                        'type': 'integer',
                        'description': 'The maximum number of conversation turns'
                    }
                },
                'required': ['chat_name', 'task_description', 'num_participants', 'max_turns']
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, chat_name, task_description, num_participants, max_turns):
        # Create a directory for the group chats
        group_chats_dir = "group_chats"
        os.makedirs(group_chats_dir, exist_ok=True)

        # Create a unique directory for the group chat
        chat_dir = os.path.join(group_chats_dir, chat_name.lower().replace(' ', '_'))
        os.makedirs(chat_dir, exist_ok=True)

        # Create a config directory for the group chat
        chat_config_dir = os.path.join(chat_dir, "config")
        os.makedirs(chat_config_dir, exist_ok=True)

        # Copy the api_keys.json file to the group chat's config directory
        api_keys_src = os.path.join("config", "api_keys.json")
        api_keys_dst = os.path.join(chat_config_dir, "api_keys.json")
        if os.path.exists(api_keys_src):
            shutil.copy(api_keys_src, api_keys_dst)
        else:
            print(f"Warning: api_keys.json not found at {api_keys_src}. You may need to create this file manually.")

        # Save the group chat configuration
        chat_config_file = os.path.join(chat_dir, "chat_config.json")
        chat_config = {
            'chat_name': chat_name,
            'task_description': task_description,
            'num_participants': num_participants,
            'max_turns': max_turns
        }
        with open(chat_config_file, 'w') as file:
            json.dump(chat_config, file, indent=2)

        # Generate the group chat code
        group_chat_code = self.generate_group_chat_code(chat_name, task_description, num_participants, max_turns)

        # Save the group chat code to a file in the group chat's directory
        chat_file_path = os.path.join(chat_dir, "group_chat.py")
        with open(chat_file_path, 'w', encoding='utf-8') as file:
            file.write(group_chat_code)

        return f"The {chat_name} group chat has been created successfully in the '{chat_dir}' directory."

    def generate_group_chat_code(self, chat_name, task_description, num_participants, max_turns):
        return f'''
import json
import sys
from openai import AzureOpenAI
import autogen
from autogen.agentchat.contrib.agent_builder import AgentBuilder

def load_api_keys(api_keys_path='config/api_keys.json'):
    try:
        with open(api_keys_path, 'r') as api_keys_file:
            return json.load(api_keys_file)
    except FileNotFoundError:
        print(f"Error: API keys file '{{api_keys_path}}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in API keys file '{{api_keys_path}}'.")
        sys.exit(1)

def load_chat_config(chat_config_path='chat_config.json'):
    try:
        with open(chat_config_path, 'r') as chat_config_file:
            return json.load(chat_config_file)
    except FileNotFoundError:
        print(f"Error: Chat configuration file '{{chat_config_path}}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in chat configuration file '{{chat_config_path}}'.")
        sys.exit(1)

def create_azure_openai_client(api_keys):
    return AzureOpenAI(
        api_key=api_keys['azure_openai_api_key'],
        api_version=api_keys['azure_openai_api_version'],
        azure_endpoint=api_keys['azure_openai_endpoint']
    )

def get_default_llm_config(api_keys):
    return {{
        "model": "gpt-4o",  # You may want to make this configurable
        "temperature": 0.7,
        "max_tokens": 2000,
        "azure_deployment": "gpt-4o",  # You may want to make this configurable
        "azure_endpoint": api_keys['azure_openai_endpoint'],
        "api_key": api_keys['azure_openai_api_key'],
        "api_type": "azure",
        "api_version": api_keys['azure_openai_api_version']
    }}

def main():
    # Load configurations
    api_keys = load_api_keys()
    chat_config = load_chat_config()

    # Set up Azure OpenAI client
    client = create_azure_openai_client(api_keys)

    # Configure the default LLM settings
    default_llm_config = get_default_llm_config(api_keys)

    # Create participants
    participants = []
    for i in range(chat_config['num_participants']):
        participant = autogen.AssistantAgent(
            name=f"Participant_{{i+1}}",
            system_message=f"You are Participant {{i+1}} in this group chat. Your task is: {{chat_config['task_description']}}",
            llm_config=default_llm_config,
        )
        participants.append(participant)

    # Create GroupChat and GroupChatManager
    group_chat = autogen.GroupChat(agents=participants, messages=[], max_round=chat_config['max_turns'])
    manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=default_llm_config)

    # Initiate the chat
    result = manager.initiate_chat(manager, message=chat_config['task_description'])
    print(result)

if __name__ == "__main__":
    main()
'''

    def list_group_chats(self):
        group_chats_dir = "group_chats"
        if not os.path.exists(group_chats_dir):
            return "No group chats have been created yet."

        chats = os.listdir(group_chats_dir)
        if not chats:
            return "No group chats have been created yet."

        return "Created Group Chats:\n" + "\n".join(chats)

    def delete_group_chat(self, chat_name):
        chat_dir = os.path.join("group_chats", chat_name.lower().replace(' ', '_'))
        if not os.path.exists(chat_dir):
            return f"Group chat '{chat_name}' not found."

        try:
            shutil.rmtree(chat_dir)
            return f"Group chat '{chat_name}' has been deleted successfully."
        except Exception as e:
            return f"An error occurred while deleting the group chat: {str(e)}"

    def update_group_chat(self, chat_name, new_task_description):
        chat_dir = os.path.join("group_chats", chat_name.lower().replace(' ', '_'))
        if not os.path.exists(chat_dir):
            return f"Group chat '{chat_name}' not found."

        config_file = os.path.join(chat_dir, "chat_config.json")
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)
            
            config['task_description'] = new_task_description
            
            with open(config_file, 'w') as file:
                json.dump(config, file, indent=2)
            
            return f"Group chat '{chat_name}' has been updated successfully."
        except Exception as e:
            return f"An error occurred while updating the group chat: {str(e)}"

    def get_group_chat_info(self, chat_name):
        chat_dir = os.path.join("group_chats", chat_name.lower().replace(' ', '_'))
        if not os.path.exists(chat_dir):
            return f"Group chat '{chat_name}' not found."

        config_file = os.path.join(chat_dir, "chat_config.json")
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)
            
            return f"Chat Name: {config['chat_name']}\nTask Description: {config['task_description']}\nNumber of Participants: {config['num_participants']}\nMax Turns: {config['max_turns']}"
        except Exception as e:
            return f"An error occurred while retrieving group chat information: {str(e)}"

    def run_group_chat(self, chat_name):
        chat_dir = os.path.join("group_chats", chat_name.lower().replace(' ', '_'))
        if not os.path.exists(chat_dir):
            return f"Group chat '{chat_name}' not found."

        chat_file_path = os.path.join(chat_dir, "group_chat.py")
        try:
            result = subprocess.run(["python", chat_file_path], capture_output=True, text=True, check=True)
            return f"Group chat '{chat_name}' executed successfully. Output:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            return f"An error occurred while running the group chat: {e.output}"

    def backup_group_chat(self, chat_name, backup_dir="group_chat_backups"):
        source_dir = os.path.join("group_chats", chat_name.lower().replace(' ', '_'))
        if not os.path.exists(source_dir):
            return f"Group chat '{chat_name}' not found."

        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, f"{chat_name.lower().replace(' ', '_')}_backup")

        try:
            shutil.copytree(source_dir, backup_path)
            return f"Group chat '{chat_name}' has been backed up successfully to {backup_path}."
        except Exception as e:
            return f"An error occurred while backing up the group chat: {str(e)}"

    def restore_group_chat(self, chat_name, backup_dir="group_chat_backups"):
        backup_path = os.path.join(backup_dir, f"{chat_name.lower().replace(' ', '_')}_backup")
        if not os.path.exists(backup_path):
            return f"Backup for group chat '{chat_name}' not found."

        target_dir = os.path.join("group_chats", chat_name.lower().replace(' ', '_'))

        try:
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            shutil.copytree(backup_path, target_dir)
            return f"Group chat '{chat_name}' has been restored successfully from backup."
        except Exception as e:
            return f"An error occurred while restoring the group chat: {str(e)}"
