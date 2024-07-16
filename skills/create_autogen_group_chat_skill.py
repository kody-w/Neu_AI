import os
import json
import shutil
from skills.basic_skill import BasicSkill
import autogen
from openai import AzureOpenAI

class AutoGenGroupChatSkill(BasicSkill):
    def __init__(self):
        self.name = 'AutoGenGroupChat'
        self.metadata = {
            'name': self.name,
            'description': 'A skill to create, manage, and run AutoGen-based group chats.',
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
        # Load API keys
        api_keys = self.load_api_keys()

        # Set up Azure OpenAI client
        client = self.create_azure_openai_client(api_keys)

        # Configure the default LLM settings
        default_llm_config = self.get_default_llm_config(api_keys)

        # Create participants
        participants = []
        for i in range(num_participants):
            participant = autogen.AssistantAgent(
                name=f"Participant_{i+1}",
                system_message=f"You are Participant {i+1} in this group chat. Your task is: {task_description}",
                llm_config=default_llm_config,
            )
            participants.append(participant)

        # Create GroupChat and GroupChatManager
        group_chat = autogen.GroupChat(agents=participants, messages=[], max_round=max_turns)
        manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=default_llm_config)

        # Initiate the chat
        result = manager.initiate_chat(manager, message=task_description)

        # Save the chat results and configuration
        self.save_chat_results(chat_name, result)
        self.save_chat_config(chat_name, task_description, num_participants, max_turns)

        return f"Group chat '{chat_name}' executed successfully. Results:\n{result}"

    def load_api_keys(self, api_keys_path='config/api_keys.json'):
        try:
            with open(api_keys_path, 'r') as api_keys_file:
                return json.load(api_keys_file)
        except FileNotFoundError:
            raise Exception(f"Error: API keys file '{api_keys_path}' not found.")
        except json.JSONDecodeError:
            raise Exception(f"Error: Invalid JSON in API keys file '{api_keys_path}'.")

    def create_azure_openai_client(self, api_keys):
        return AzureOpenAI(
            api_key=api_keys['azure_openai_api_key'],
            api_version=api_keys['azure_openai_api_version'],
            azure_endpoint=api_keys['azure_openai_endpoint']
        )

    def get_default_llm_config(self, api_keys):
        return {
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 2000,
            "azure_deployment": "gpt-4o",
            "azure_endpoint": api_keys['azure_openai_endpoint'],
            "api_key": api_keys['azure_openai_api_key'],
            "api_type": "azure",
            "api_version": api_keys['azure_openai_api_version']
        }

    def save_chat_results(self, chat_name, result):
        group_chats_dir = "group_chats"
        os.makedirs(group_chats_dir, exist_ok=True)
        chat_dir = os.path.join(group_chats_dir, chat_name.lower().replace(' ', '_'))
        os.makedirs(chat_dir, exist_ok=True)
        
        results_file = os.path.join(chat_dir, "chat_results.txt")
        with open(results_file, 'w', encoding='utf-8') as file:
            file.write(str(result))

    def save_chat_config(self, chat_name, task_description, num_participants, max_turns):
        group_chats_dir = "group_chats"
        chat_dir = os.path.join(group_chats_dir, chat_name.lower().replace(' ', '_'))
        os.makedirs(chat_dir, exist_ok=True)

        config_file = os.path.join(chat_dir, "chat_config.json")
        config = {
            'chat_name': chat_name,
            'task_description': task_description,
            'num_participants': num_participants,
            'max_turns': max_turns
        }
        with open(config_file, 'w') as file:
            json.dump(config, file, indent=2)

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