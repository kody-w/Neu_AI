import os
import json
import shutil
import re
from skills.basic_skill import BasicSkill
import autogen
from openai import AzureOpenAI
from datetime import datetime
import logging


class DynamicAutoGenGroupChatSkill(BasicSkill):
    def __init__(self):
        self.name = 'DynamicAutoGenGroupChat'
        self.metadata = {
            'name': self.name,
            'description': 'A skill to create and run dynamic AutoGen-based group chats with specialized agent roles, detailed reporting, and process logging.',
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
                    'roles': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'role': {'type': 'string'},
                                'prompt': {'type': 'string'}
                            },
                            'required': ['name', 'role', 'prompt']
                        },
                        'description': 'An array of specialized roles for the group chat'
                    },
                    'manager_prompt': {
                        'type': 'string',
                        'description': 'The prompt for the group manager role'
                    },
                    'max_turns': {
                        'type': 'integer',
                        'description': 'The maximum number of conversation turns'
                    },
                    'temperature': {
                        'type': 'number',
                        'description': 'The temperature setting for the LLM'
                    },
                    'max_tokens': {
                        'type': 'integer',
                        'description': 'The maximum number of tokens for each LLM response'
                    }
                },
                'required': ['chat_name', 'task_description', 'roles', 'manager_prompt', 'max_turns', 'temperature', 'max_tokens']
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.setup_logging()

    def setup_logging(self):
        log_dir = "group_chat_logs"
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(filename=os.path.join(log_dir, 'group_chat_process.log'),
                            level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def sanitize_name(self, name):
        # Remove any characters that are not alphanumeric, underscore, or hyphen
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', name)
        # Ensure the name starts with a letter or underscore
        if not sanitized or not sanitized[0].isalpha() and sanitized[0] != '_':
            sanitized = '_' + sanitized
        return sanitized

    def perform(self, chat_name, task_description, roles, manager_prompt, max_turns, temperature, max_tokens):
        try:
            logging.info(f"Starting group chat: {chat_name}")
            logging.info(f"Task description: {task_description}")

            # Load API keys
            api_keys = self.load_api_keys()
            logging.info("API keys loaded successfully")

            # Set up Azure OpenAI client
            client = self.create_azure_openai_client(api_keys)
            logging.info("Azure OpenAI client created")

            # Configure the default LLM settings
            default_llm_config = self.get_default_llm_config(
                api_keys, temperature, max_tokens)
            logging.info(f"LLM config set up with temperature {temperature} and max_tokens {max_tokens}")

            # Create specialized agents
            agents = self.create_specialized_agents(roles, default_llm_config)
            logging.info(f"Created {len(agents)} specialized agents")

            # Create a group manager agent
            group_manager = autogen.AssistantAgent(
                name=self.sanitize_name("GroupManager"),
                system_message=f"You are the group manager. {
                    manager_prompt} Ensure the group stays on task and delivers what is expected based on this goal: {task_description}",
                llm_config=default_llm_config,
            )
            logging.info("Group manager created")

            # Create a user proxy agent
            user_proxy = autogen.UserProxyAgent(
                name=self.sanitize_name("UserProxy"),
                system_message="You are a user proxy that will help guide the conversation and ensure the task is completed.",
                human_input_mode="NEVER",
                llm_config=default_llm_config,
                # Disable Docker usage
                code_execution_config={"use_docker": False}
            )
            logging.info("User proxy created")

            # Create GroupChat and GroupChatManager
            group_chat = autogen.GroupChat(
                agents=agents + [group_manager, user_proxy], messages=[], max_round=max_turns)
            manager = autogen.GroupChatManager(
                groupchat=group_chat, llm_config=default_llm_config)
            logging.info("GroupChat and GroupChatManager created")

            # Initiate the chat
            logging.info("Initiating group chat")
            chat_result = user_proxy.initiate_chat(
                manager, message=task_description)
            logging.info("Group chat completed")

            # Generate and save the report
            report = self.generate_report(
                chat_name, task_description, roles, manager_prompt, max_turns, temperature, max_tokens, chat_result)
            report_path = self.save_report(chat_name, report)
            logging.info(f"Report generated and saved at: {report_path}")

            # Save the chat results and configuration
            self.save_chat_results(chat_name, chat_result)
            self.save_chat_config(chat_name, task_description, roles,
                                  manager_prompt, max_turns, temperature, max_tokens)
            logging.info("Chat results and configuration saved")

            return f"Group chat '{chat_name}' executed successfully. Report saved at: {report_path}"
        except Exception as e:
            logging.error(f"An error occurred while executing the group chat: {
                          str(e)}", exc_info=True)
            return f"An error occurred while executing the group chat: {str(e)}"

    def create_specialized_agents(self, roles, llm_config):
        agents = []
        for role in roles:
            sanitized_name = self.sanitize_name(role['name'])
            agent = autogen.AssistantAgent(
                name=sanitized_name,
                system_message=f"You are the {role['role']}. {role['prompt']}",
                llm_config=llm_config,
            )
            agents.append(agent)
            logging.info(f"Created agent: {sanitized_name} as {role['role']}")
        return agents

    def generate_report(self, chat_name, task_description, roles, manager_prompt, max_turns, temperature, max_tokens, chat_result):
        report = {
            "chat_name": chat_name,
            "task_description": task_description,
            "execution_time": datetime.now().isoformat(),
            "configuration": {
                "roles": roles,
                "manager_prompt": manager_prompt,
                "max_turns": max_turns,
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            "chat_summary": self.summarize_chat(chat_result),
            "full_chat_log": chat_result
        }
        return report

    def summarize_chat(self, chat_result):
        total_messages = len(chat_result)
        participants = set(msg['name'] for msg in chat_result if 'name' in msg)
        return {
            "total_messages": total_messages,
            "participants": list(participants),
            "last_message": chat_result[-1]['content'] if chat_result else "No messages"
        }

    def save_report(self, chat_name, report):
        reports_dir = "group_chat_reports"
        os.makedirs(reports_dir, exist_ok=True)
        report_filename = f"{chat_name.lower().replace(' ', '_')}_report_{
            datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(reports_dir, report_filename)
        with open(report_path, 'w', encoding='utf-8') as file:
            json.dump(report, file, indent=2, ensure_ascii=False)
        return report_path

    def load_api_keys(self, api_keys_path='config/api_keys.json'):
        try:
            with open(api_keys_path, 'r') as api_keys_file:
                return json.load(api_keys_file)
        except FileNotFoundError:
            logging.error(f"API keys file '{api_keys_path}' not found.")
            raise Exception(f"Error: API keys file '{
                            api_keys_path}' not found.")
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in API keys file '{api_keys_path}'.")
            raise Exception(f"Error: Invalid JSON in API keys file '{
                            api_keys_path}'.")

    def create_azure_openai_client(self, api_keys):
        return AzureOpenAI(
            api_key=api_keys['azure_openai_api_key'],
            api_version=api_keys['azure_openai_api_version'],
            azure_endpoint=api_keys['azure_openai_endpoint']
        )

    def get_default_llm_config(self, api_keys, temperature, max_tokens):
        return {
            "model": "gpt-4o",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "azure_deployment": "gpt-4o",
            "azure_endpoint": api_keys['azure_openai_endpoint'],
            "api_key": api_keys['azure_openai_api_key'],
            "api_type": "azure",
            "api_version": api_keys['azure_openai_api_version']
        }

    def save_chat_results(self, chat_name, result):
        group_chats_dir = "group_chats"
        os.makedirs(group_chats_dir, exist_ok=True)
        chat_dir = os.path.join(
            group_chats_dir, chat_name.lower().replace(' ', '_'))
        os.makedirs(chat_dir, exist_ok=True)

        results_file = os.path.join(chat_dir, "chat_results.json")
        with open(results_file, 'w', encoding='utf-8') as file:
            json.dump(result, file, indent=2, ensure_ascii=False)

    def save_chat_config(self, chat_name, task_description, roles, manager_prompt, max_turns, temperature, max_tokens):
        group_chats_dir = "group_chats"
        chat_dir = os.path.join(
            group_chats_dir, chat_name.lower().replace(' ', '_'))
        os.makedirs(chat_dir, exist_ok=True)

        config_file = os.path.join(chat_dir, "chat_config.json")
        config = {
            'chat_name': chat_name,
            'task_description': task_description,
            'roles': roles,
            'manager_prompt': manager_prompt,
            'max_turns': max_turns,
            'temperature': temperature,
            'max_tokens': max_tokens
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
        chat_dir = os.path.join(
            "group_chats", chat_name.lower().replace(' ', '_'))
        if not os.path.exists(chat_dir):
            return f"Group chat '{chat_name}' not found."

        try:
            shutil.rmtree(chat_dir)
            return f"Group chat '{chat_name}' has been deleted successfully."
        except Exception as e:
            return f"An error occurred while deleting the group chat: {str(e)}"

    def update_group_chat(self, chat_name, new_task_description):
        chat_dir = os.path.join(
            "group_chats", chat_name.lower().replace(' ', '_'))
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
        chat_dir = os.path.join(
            "group_chats", chat_name.lower().replace(' ', '_'))
        if not os.path.exists(chat_dir):
            return f"Group chat '{chat_name}' not found."

        config_file = os.path.join(chat_dir, "chat_config.json")
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)

            info = f"Chat Name: {config['chat_name']}\n"
            info += f"Task Description: {config['task_description']}\n"
            info += f"Number of Roles: {len(config['roles'])}\n"
            info += f"Roles:\n"
            for role in config['roles']:
                info += f"  - {role['name']} ({role['role']})\n"
            info += f"Max Turns: {config['max_turns']}\n"
            info += f"Temperature: {config['temperature']}\n"
            info += f"Max Tokens: {config['max_tokens']}\n"
            return info
        except Exception as e:
            return f"An error occurred while retrieving group chat information: {str(e)}"

    def backup_group_chat(self, chat_name, backup_dir="group_chat_backups"):
        source_dir = os.path.join(
            "group_chats", chat_name.lower().replace(' ', '_'))
        if not os.path.exists(source_dir):
            return f"Group chat '{chat_name}' not found."

        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(
            backup_dir, f"{chat_name.lower().replace(' ', '_')}_backup")

        try:
            shutil.copytree(source_dir, backup_path)
            return f"Group chat '{chat_name}' has been backed up successfully to {backup_path}."
        except Exception as e:
            return f"An error occurred while backing up the group chat: {str(e)}"

    def restore_group_chat(self, chat_name, backup_dir="group_chat_backups"):
        backup_path = os.path.join(
            backup_dir, f"{chat_name.lower().replace(' ', '_')}_backup")
        if not os.path.exists(backup_path):
            return f"Backup for group chat '{chat_name}' not found."

        target_dir = os.path.join(
            "group_chats", chat_name.lower().replace(' ', '_'))

        try:
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            shutil.copytree(backup_path, target_dir)
            return f"Group chat '{chat_name}' has been restored successfully from backup."
        except Exception as e:
            return f"An error occurred while restoring the group chat: {str(e)}"

# End of DynamicAutoGenGroupChatSkill class
