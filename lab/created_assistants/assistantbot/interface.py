
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
    filtered_text = re.sub(r'[^a-zA-Z0-9\s\.,!?]', '', text)
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
