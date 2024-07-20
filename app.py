from flask import Flask, request, render_template, jsonify
import json
from assistant import Assistant
from skills.basic_skill import BasicSkill
import importlib
import inspect
import os

app = Flask(__name__)
app.static_folder = 'static'

# Load assistant configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

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
assistant = Assistant(declared_skills)

@app.route('/')
def index():
    try:
        with open('memory.json', 'r') as memory_file:
            memories = json.load(memory_file)
    except FileNotFoundError:
        memories = {'error': 'Memory file not found.'}

    return render_template('index.html', memories=memories, assistant=assistant, assistant_name=config["assistant_name"])

@app.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json['user_input']
    if user_input is not None and user_input.strip() != "":
        assistant_response, skill_logs = assistant.get_response(user_input.strip())
        return jsonify({'response': assistant_response, 'skill_logs': skill_logs})
    else:
        return jsonify({'response': '', 'skill_logs': ''}), 400

if __name__ == '__main__':
   app.run(debug=True)