import json
import sys
import os
import importlib
import inspect
import re
import argparse
from termcolor import colored, cprint
from assistant import Assistant
from skills.basic_skill import BasicSkill
import ssl

def configure_ssl():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

def load_skills_from_folder(verbose_mode=False):
    files_in_skills_directory = os.listdir("./skills")
    skill_files = [f for f in files_in_skills_directory if f.endswith(".py") and f not in ["__init__.py", "basic_skill.py"]]

    declared_skills = []
    for skill_file in skill_files:
        module_name = skill_file[:-3]
        try:
            module = importlib.import_module(f'skills.{module_name}')
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BasicSkill) and obj is not BasicSkill:
                    try:
                        skill_instance = obj()
                        declared_skills.append(skill_instance)
                        if verbose_mode:
                            print(f"Successfully loaded skill: {obj.__name__}")
                    except Exception as e:
                        if verbose_mode:
                            print(f"Error initializing skill {obj.__name__}: {str(e)}")
        except Exception as e:
            if verbose_mode:
                print(f"Error loading module {module_name}: {str(e)}")

    return declared_skills

def filter_text(text):
    filtered_text = re.sub(r'[^a-zA-Z0-9\s\.,!?]', '', text)
    return filtered_text

def speak(response, assistant_name):
    text, additional_output = response

    filtered_text = filter_text(text)
    cprint(assistant_name + f":🌐📞 {text}", 'cyan')

    if additional_output:
        print(additional_output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the assistant.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode with debug output.')
    args = parser.parse_args()
    verbose_mode = args.verbose

    configure_ssl()
    declared_skills = load_skills_from_folder(verbose_mode=verbose_mode)
    if verbose_mode:
        print(f"Loaded {len(declared_skills)} skills successfully.")

    # Load configuration from config.json
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    assistant_name = config['assistant_name']
    cprint(f"Welcome to {assistant_name}, your command line assistant!", 'yellow', 'on_red', attrs=['bold', 'blink'])
    cprint("Type 'help' for a list of commands or 'exit' to quit.", 'yellow')

    assistant = Assistant(declared_skills)
    conversation_history = []

    while True:
        user_input = input(colored("User>😎📞", 'green'))
        if user_input.lower() == 'exit':
            cprint(f"Goodbye from {assistant_name}! 👋", 'yellow')
            break
        else:
            user_sentence = user_input

        conversation_history.append({"role": "user", "content": user_sentence})

        assistant_response, skill_logs = assistant.get_response(user_sentence, conversation_history)

        conversation_history.append({"role": "assistant", "content": assistant_response})

        if verbose_mode and skill_logs:
            cprint(skill_logs, 'white')

        speak((assistant_response, None), assistant_name)
