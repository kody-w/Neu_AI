from openai import OpenAI
from config.settings import OPENAI_KEY
from assistant import Assistant
from skills.basic_skill import BasicSkill
import os
import importlib
import inspect

# Initialize OpenAI client with the API key
OPENAI_CLIENT = OpenAI(api_key=OPENAI_KEY)

def load_skills_from_folder():
    files_in_skills_directory = os.listdir("./skills")
    skill_files = []
    for file in files_in_skills_directory:
        if not file.endswith(".py"):
            continue
        if file in ["__init__.py", "basic_skill.py"]:
            continue
        skill_files.append(file)
    skill_module_names = [file[:-3] for file in skill_files]
    declared_skills = []
    for skill_name in skill_module_names:
        module = importlib.import_module('skills.' + skill_name)
        for name, member in inspect.getmembers(module):
            if inspect.isclass(member) and issubclass(member, BasicSkill) and member is not BasicSkill:
                declared_skills.append(member())
    return declared_skills

declared_skills = load_skills_from_folder()
assistant = Assistant("config/api_keys.json", declared_skills)

def make_api_call(messages):
    # Create a completion using the OpenAI API
    response = OPENAI_CLIENT.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        functions=assistant.get_skill_metadata(),
        function_call="auto"
    )
    return response.choices[0].message.content

def get_response(context):
    # Get a response from the assistant based on the current context
    assistant_response, skill_logs = assistant.get_response(context[-1]["content"])

    # Return only the assistant's response as a string
    return assistant_response