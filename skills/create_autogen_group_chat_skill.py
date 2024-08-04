import os
import json
import shutil
import subprocess
from skills.basic_skill import BasicSkill
import autogen


class AutoGenGroupChatSkill(BasicSkill):
    def __init__(self):
        self.name = 'CreateAutoGenGroupChatSkill'
        self.metadata = {
            'name': self.name,
            'description': 'A skill to create and manage ultra-customizable AutoGen-based group chats with per-agent parameter tuning, early termination capability, and a final report generation.',
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
                    'participants': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'role': {'type': 'string'},
                                'prompt': {'type': 'string'},
                                'model': {'type': 'string'},
                                'temperature': {'type': 'number'},
                                'max_tokens': {'type': 'integer'},
                                'top_p': {'type': 'number'},
                                'frequency_penalty': {'type': 'number'},
                                'presence_penalty': {'type': 'number'}
                            },
                            'required': ['name', 'role', 'prompt']
                        },
                        'description': 'An array of participant configurations with per-agent LLM settings'
                    },
                    'max_turns': {
                        'type': 'integer',
                        'description': 'The maximum number of conversation turns'
                    },
                    'user_proxy': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'prompt': {'type': 'string'},
                            'human_input_mode': {'type': 'string'},
                            'model': {'type': 'string'},
                            'temperature': {'type': 'number'},
                            'max_tokens': {'type': 'integer'},
                            'top_p': {'type': 'number'},
                            'frequency_penalty': {'type': 'number'},
                            'presence_penalty': {'type': 'number'}
                        },
                        'description': 'Configuration for the user proxy agent'
                    },
                    'manager': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'prompt': {'type': 'string'},
                            'model': {'type': 'string'},
                            'temperature': {'type': 'number'},
                            'max_tokens': {'type': 'integer'},
                            'top_p': {'type': 'number'},
                            'frequency_penalty': {'type': 'number'},
                            'presence_penalty': {'type': 'number'}
                        },
                        'description': 'Configuration for the group chat manager'
                    },
                    'report_agent': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'prompt': {'type': 'string'},
                            'model': {'type': 'string'},
                            'temperature': {'type': 'number'},
                            'max_tokens': {'type': 'integer'},
                            'top_p': {'type': 'number'},
                            'frequency_penalty': {'type': 'number'},
                            'presence_penalty': {'type': 'number'}
                        },
                        'description': 'Configuration for the report generation agent'
                    },
                    'default_model': {
                        'type': 'string',
                        'description': 'The default Azure OpenAI model to use',
                        'default': 'gpt-4o-mini'
                    },
                    'default_azure_deployment': {
                        'type': 'string',
                        'description': 'The default Azure deployment name for the model',
                        'default': 'gpt-4o-mini'
                    },
                    'allow_early_termination': {
                        'type': 'boolean',
                        'description': 'Whether to allow the manager to end the chat early if the task is completed',
                        'default': True
                    }
                },
                'required': ['chat_name', 'task_description', 'participants', 'max_turns']
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, chat_name, task_description, participants, max_turns, user_proxy=None, manager=None, report_agent=None, default_model='gpt-4o-mini', default_azure_deployment='gpt-4o-mini', allow_early_termination=True):
        group_chats_dir = "group_chats"
        os.makedirs(group_chats_dir, exist_ok=True)

        chat_dir = os.path.join(
            group_chats_dir, chat_name.lower().replace(' ', '_'))
        os.makedirs(chat_dir, exist_ok=True)

        chat_config_dir = os.path.join(chat_dir, "config")
        os.makedirs(chat_config_dir, exist_ok=True)

        api_keys_src = os.path.join("config", "api_keys.json")
        api_keys_dst = os.path.join(chat_config_dir, "api_keys.json")
        if os.path.exists(api_keys_src):
            shutil.copy(api_keys_src, api_keys_dst)
        else:
            print(
                f"Warning: api_keys.json not found at {api_keys_src}. You may need to create this file manually.")

        chat_config_file = os.path.join(chat_dir, "chat_config.json")
        chat_config = {
            'chat_name': chat_name,
            'task_description': task_description,
            'participants': participants,
            'max_turns': max_turns,
            'user_proxy': user_proxy or {
                'name': 'UserProxy',
                'prompt': 'You are a user proxy that will help guide the conversation and ensure the task is completed.',
                'human_input_mode': 'NEVER'
            },
            'manager': manager or {
                'name': 'Manager',
                'prompt': 'You are the manager of this group chat. Ensure the group stays on task and delivers what is expected. You can end the chat early if you believe the task is completed satisfactorily.'
            },
            'report_agent': report_agent or {
                'name': 'ReportAgent',
                'prompt': 'You are responsible for generating a comprehensive report based on the group chat discussion. Summarize key points, decisions, and outcomes related to the task.',
                'model': default_model,
                'temperature': 0.7,
                'max_tokens': 2000
            },
            'default_model': default_model,
            'default_azure_deployment': default_azure_deployment,
            'allow_early_termination': allow_early_termination
        }
        with open(chat_config_file, 'w') as file:
            json.dump(chat_config, file, indent=2)

        group_chat_code = self.generate_group_chat_code()

        chat_file_path = os.path.join(chat_dir, "group_chat.py")
        with open(chat_file_path, 'w', encoding='utf-8') as file:
            file.write(group_chat_code)

        return f"The {chat_name} group chat has been created successfully in the '{chat_dir}' directory."

    def generate_group_chat_code(self):
        return '''
import json
import sys
from openai import AzureOpenAI
import autogen

def load_api_keys(api_keys_path='config/api_keys.json'):
    try:
        with open(api_keys_path, 'r') as api_keys_file:
            return json.load(api_keys_file)
    except FileNotFoundError:
        print(f"Error: API keys file '{api_keys_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in API keys file '{api_keys_path}'.")
        sys.exit(1)

def load_chat_config(chat_config_path='chat_config.json'):
    try:
        with open(chat_config_path, 'r') as chat_config_file:
            return json.load(chat_config_file)
    except FileNotFoundError:
        print(f"Error: Chat configuration file '{chat_config_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in chat configuration file '{chat_config_path}'.")
        sys.exit(1)

def create_azure_openai_client(api_keys):
    return AzureOpenAI(
        api_key=api_keys['azure_openai_api_key'],
        api_version=api_keys['azure_openai_api_version'],
        azure_endpoint=api_keys['azure_openai_endpoint']
    )

def get_llm_config(api_keys, agent_config, chat_config):
    return {
        "model": agent_config.get('model', chat_config['default_model']),
        "temperature": agent_config.get('temperature', 0.7),
        "max_tokens": agent_config.get('max_tokens', 2000),
        "top_p": agent_config.get('top_p', 0.95),
        "frequency_penalty": agent_config.get('frequency_penalty', 0),
        "presence_penalty": agent_config.get('presence_penalty', 0),
        "azure_deployment": agent_config.get('model', chat_config['default_azure_deployment']),
        "azure_endpoint": api_keys['azure_openai_endpoint'],
        "api_key": api_keys['azure_openai_api_key'],
        "api_type": "azure",
        "api_version": api_keys['azure_openai_api_version']
    }

class EarlyTerminationGroupChatManager(autogen.GroupChatManager):
    def __init__(self, allow_early_termination=True, **kwargs):
        super().__init__(**kwargs)
        self.allow_early_termination = allow_early_termination

    def process_message(self, message, sender, silent):
        if self.allow_early_termination and "TASK_COMPLETED" in message.upper():
            print("Task completed. Ending the chat early.")
            return False  # This will end the chat
        return super().process_message(message, sender, silent)

def generate_report(report_agent, chat_history, task_description):
    report_prompt = f"""
    Task Description: {task_description}

    Chat History:
    {chat_history}

    Based on the above task description and chat history, generate a comprehensive report summarizing the key points, decisions, and outcomes. The report should be well-structured, clear, and provide valuable insights derived from the group chat discussion.
    """
    
    report = report_agent.generate_response(report_prompt)
    return report

def save_report(report, chat_name):
    report_file_path = f"group_chats/{chat_name.lower().replace(' ', '_')}/final_report.md"
    with open(report_file_path, 'w', encoding='utf-8') as file:
        file.write(report)
    print(f"Final report saved to: {report_file_path}")

def main():
    api_keys = load_api_keys()
    chat_config = load_chat_config()

    client = create_azure_openai_client(api_keys)

    participants = []
    for participant in chat_config['participants']:
        llm_config = get_llm_config(api_keys, participant, chat_config)
        agent = autogen.AssistantAgent(
            name=participant['name'],
            system_message=f"You are {participant['role']}. {participant['prompt']}",
            llm_config=llm_config,
        )
        participants.append(agent)

    user_proxy_config = get_llm_config(api_keys, chat_config['user_proxy'], chat_config)
    user_proxy = autogen.UserProxyAgent(
        name=chat_config['user_proxy']['name'],
        system_message=chat_config['user_proxy']['prompt'],
        human_input_mode=chat_config['user_proxy']['human_input_mode'],
        llm_config=user_proxy_config,
        code_execution_config={"use_docker": False}
    )

    manager_config = get_llm_config(api_keys, chat_config['manager'], chat_config)
    group_chat = autogen.GroupChat(agents=participants + [user_proxy], messages=[], max_round=chat_config['max_turns'])
    manager = EarlyTerminationGroupChatManager(
        groupchat=group_chat,
        llm_config=manager_config,
        system_message=chat_config['manager']['prompt'],
        allow_early_termination=chat_config['allow_early_termination']
    )

    report_agent_config = get_llm_config(api_keys, chat_config['report_agent'], chat_config)
    report_agent = autogen.AssistantAgent(
        name=chat_config['report_agent']['name'],
        system_message=chat_config['report_agent']['prompt'],
        llm_config=report_agent_config,
    )

    result = manager.initiate_chat(manager, message=chat_config['task_description'])
    print(result)

    # Generate and save the report
    chat_history = "\n".join([f"{msg['sender']}: {msg['content']}" for msg in group_chat.messages])
    report = generate_report(report_agent, chat_history, chat_config['task_description'])
    save_report(report, chat_config['chat_name'])

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
        chat_dir = os.path.join(
            "group_chats", chat_name.lower().replace(' ', '_'))
        if not os.path.exists(chat_dir):
            return f"Group chat '{chat_name}' not found."

        try:
            shutil.rmtree(chat_dir)
            return f"Group chat '{chat_name}' has been deleted successfully."
        except Exception as e:
            return f"An error occurred while deleting the group chat: {str(e)}"

    def update_group_chat(self, chat_name, new_config):
        chat_dir = os.path.join(
            "group_chats", chat_name.lower().replace(' ', '_'))
        if not os.path.exists(chat_dir):
            return f"Group chat '{chat_name}' not found."

        config_file = os.path.join(chat_dir, "chat_config.json")
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)

            config.update(new_config)

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
            info += f"Number of Participants: {len(config['participants'])}\n"
            info += "Participants:\n"
            for participant in config['participants']:
                info += f"  - {participant['name']} ({participant['role']})\n"
                info += f"    Model: {participant.get('model', 'Default')}\n"
                info += f"    Temperature: {participant.get('temperature', 'Default')}\n"
                info += f"    Max Tokens: {participant.get('max_tokens', 'Default')}\n"
            info += f"Max Turns: {config['max_turns']}\n"
            info += f"User Proxy: {config['user_proxy']['name']}\n"
            info += f"Manager: {config['manager']['name']}\n"
            info += f"Report Agent: {config['report_agent']['name']}\n"
            info += f"Default Model: {config['default_model']}\n"
            info += f"Default Azure Deployment: {config['default_azure_deployment']}\n"
            info += f"Allow Early Termination: {config['allow_early_termination']}\n"
            return info
        except Exception as e:
            return f"An error occurred while retrieving group chat information: {str(e)}"

    def run_group_chat(self, chat_name):
        chat_dir = os.path.join(
            "group_chats", chat_name.lower().replace(' ', '_'))
        if not os.path.exists(chat_dir):
            return f"Group chat '{chat_name}' not found."

        chat_file_path = os.path.join(chat_dir, "group_chat.py")
        try:
            result = subprocess.run(
                ["python", chat_file_path], capture_output=True, text=True, check=True)
            return f"Group chat '{chat_name}' executed successfully. Output:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            return f"An error occurred while running the group chat: {e.output}"

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

# End of AutoGenGroupChatSkill class
