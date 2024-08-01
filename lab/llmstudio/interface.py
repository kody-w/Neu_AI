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
    skills_dir = "./skills"
    skill_files = [f for f in os.listdir(skills_dir) if f.endswith(".py") and f not in ["__init__.py", "basic_skill.py"]]
    
    declared_skills = []
    for skill_file in skill_files:
        module_name = f"skills.{skill_file[:-3]}"
        module = importlib.import_module(module_name)
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BasicSkill) and obj is not BasicSkill:
                skill_instance = obj()
                declared_skills.append(skill_instance)
                print(f"Loaded skill: {skill_instance.name}")
    
    return declared_skills

def filter_text(text):
    # Remove any characters that are not alphanumeric, space, or punctuation
    filtered_text = re.sub(r'[^a-zA-Z0-9\s\.,!?]', '', text)
    return filtered_text

def speak(response, assistant_name):
    text, additional_output = response
    
    if additional_output:
        cprint("Skill used:", 'yellow', attrs=['bold'])
        cprint(additional_output, 'yellow')
        cprint("-" * 50, 'yellow')
    
    filtered_text = filter_text(text)
    cprint(f"{assistant_name}:🌐📞 {filtered_text}", 'cyan')

def print_help(assistant_name, skills):
    cprint(f"\n{assistant_name} Help:", 'yellow', attrs=['bold'])
    cprint("Available commands:", 'yellow')
    cprint("  exit - Exit the program", 'green')
    cprint("  help - Display this help message", 'green')
    cprint("\nAvailable skills:", 'yellow')
    for skill in skills:
        cprint(f"  {skill.name} - {skill.metadata['description']}", 'green')
        if 'aliases' in skill.metadata:
            cprint(f"    Aliases: {', '.join(skill.metadata['aliases'])}", 'cyan')
    cprint("\nYou can interact with the assistant naturally, and it will use skills when appropriate.", 'yellow')

if __name__ == "__main__":
    declared_skills = load_skills_from_folder()

    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    assistant_name = config['assistant_name']
    assistant = Assistant(declared_skills)
    
    cprint(f"Welcome to {assistant_name}, your command line assistant!", 'yellow', 'on_red', attrs=['bold', 'blink'])
    cprint("Type 'help' for a list of commands or 'exit' to quit.", 'yellow')

    conversation_history = []

    while True:
        user_input = input(colored("User>😎📞 ", 'green'))
        
        if user_input.lower() == 'exit':
            cprint(f"Goodbye from {assistant_name}! 👋", 'yellow')
            break
        elif user_input.lower() == 'help':
            print_help(assistant_name, declared_skills)
            continue
        
        conversation_history.append({"role": "user", "content": user_input})
        
        assistant_response, skill_logs = assistant.get_response(user_input, conversation_history)
        
        conversation_history.append({"role": "assistant", "content": assistant_response})
        
        speak((assistant_response, skill_logs), assistant_name)

        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]