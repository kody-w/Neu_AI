import json
import sys
import os
import importlib
import inspect
from termcolor import colored, cprint
from assistantv2 import Assistant
from skills.basic_skill import BasicSkill

def load_skills_from_folder():
    files_in_skills_directory = os.listdir("./skills")
    skill_files = [file for file in files_in_skills_directory if file.endswith(".py") and file not in ["__init__.py", "basic_skill.py"]]

    declared_skills = []
    for skill_file in skill_files:
        module_name = skill_file[:-3]
        module = importlib.import_module(f'skills.{module_name}')
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BasicSkill) and obj is not BasicSkill:
                declared_skills.append(obj())

    return declared_skills

def filter_text(text):
    return ''.join(char for char in text if char.isalnum() or char.isspace() or char in '.,!?')

def speak(response, assistant_name):
    text, additional_output = response
    filtered_text = filter_text(text)
    cprint(f"{assistant_name}:🌐📞 {text}", 'cyan')
    if additional_output:
        print(additional_output)

if __name__ == "__main__":
    declared_skills = load_skills_from_folder()

    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    assistant_name = config['assistant_name']
    assistant = Assistant(declared_skills)

    cprint(f"Welcome to {assistant_name}, your AI assistant!", 'yellow', 'on_red', attrs=['bold', 'blink'])
    cprint("Type 'exit' to quit.", 'yellow')

    while True:
        user_input = input(colored("User>😎📞", 'green'))
        
        if user_input.lower() == 'exit':
            cprint(f"Goodbye from {assistant_name}! 👋", 'yellow')
            break
        
        assistant_response = assistant.get_response(user_input)
        speak(assistant_response, assistant_name)