from flask import Flask, request, render_template, jsonify
from assistant import Assistant
import json
import os
import importlib
import inspect
from skills.basic_skill import BasicSkill

app = Flask(__name__)
app.static_folder = 'static'

# Load assistant configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

def load_skills_from_folder():
    files_in_skills_directory = os.listdir("./skills")
    skill_files = [file for file in files_in_skills_directory if file.endswith(".py") and file not in ["__init__.py", "basic_skill.py"]]

    declared_skills = []
    for skill in [file[:-3] for file in skill_files]:
        module = importlib.import_module('skills.' + skill)
        for name, member in inspect.getmembers(module):
            if inspect.isclass(member) and issubclass(member, BasicSkill) and member is not BasicSkill:
                declared_skills.append(member())

    return declared_skills

declared_skills = load_skills_from_folder()
assistant = Assistant(declared_skills)  # Create a single persistent Assistant instance

@app.route('/')
def index():
    return render_template('index.html', assistant_name=config["assistant_name"])

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json['user_input']
        conversation_history = request.json.get('conversation_history', [])
        
        if user_input is not None:
            user_input_str = str(user_input).strip()
            if user_input_str != "":
                assistant_response, skill_logs = assistant.get_response(user_input_str, conversation_history)
                
                # Update conversation history
                conversation_history.append({"role": "user", "content": user_input_str})
                conversation_history.append({"role": "assistant", "content": assistant_response})
                
                return jsonify({
                    'text': assistant_response,
                    'additional_output': skill_logs,
                    'conversation_history': conversation_history
                })
            else:
                return jsonify({
                    'text': "I'm sorry, I didn't receive any input.",
                    'additional_output': "",
                    'conversation_history': conversation_history
                }), 400
        else:
            return jsonify({
                'text': "I'm sorry, I didn't receive any input.",
                'additional_output': "",
                'conversation_history': conversation_history
            }), 400
    except Exception as e:
        print(f"Error in chat route: {str(e)}")
        return jsonify({
            'text': "An error occurred while processing your request.",
            'additional_output': str(e),
            'conversation_history': conversation_history
        }), 500

@app.route('/skills', methods=['GET'])
def get_skills():
    skills = [skill.metadata for skill in declared_skills]
    return jsonify(skills)

@app.route('/save_chat', methods=['POST'])
def save_chat():
    chat_messages = request.json.get('chatMessages', [])
    
    # Save the chat messages to a JSON file
    with open('chat_messages.json', 'w') as file:
        json.dump(chat_messages, file)
    
    return jsonify(success=True)

@app.route('/load_chat', methods=['GET'])
def load_chat():
    try:
        with open('chat_messages.json', 'r') as file:
            chat_messages = json.load(file)
        return jsonify(chat_messages)
    except FileNotFoundError:
        return jsonify([])

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)