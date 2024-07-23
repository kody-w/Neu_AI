from flask import Flask, request, render_template, jsonify, Response, redirect, url_for
from twilio.twiml.messaging_response import MessagingResponse
from config.settings import MY_PHONE
from openai_handler import get_response
import json
import feedparser
import requests
from bs4 import BeautifulSoup
import os
from interface import speak
from assistant import Assistant
from skills.basic_skill import BasicSkill
import importlib
import inspect
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.static_folder = 'static'

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Load persona content
with open("config/persona.txt", 'r') as file:
    PERSONA = file.read()

# Define initial context with system role
context = [{"role": "system", "content": PERSONA}]

# Directory for saving webpages
SAVE_DIR = 'saved_webpages'

# Modify dynamic content store to use the assistant's name from config
dynamic_content_store = f'<div class="dynamic-content"><h2>{config["assistant_name"]}</h2><p>Welcome. As {config["assistant_name"]}, I\'m here to help execute complex projects. Reach out, let\'s tackle global challenges together.</p></div>'

def load_skills_from_folder():
    files_in_skills_directory = os.listdir("./skills")
    skill_files = [file for file in files_in_skills_directory if file.endswith(".py") and file not in ["__init__.py", "basic_skill.py"]]
    skill_module_names = [file[:-3] for file in skill_files]
    declared_skills = []
    for skill in skill_module_names:
        module = importlib.import_module('skills.' + skill)
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

@app.route('/get_dynamic_content')
def get_dynamic_content():
    return dynamic_content_store

@app.route('/load_memories', methods=['GET'])
def load_memories():
    try:
        with open('memory.json', 'r') as file:
            memories = json.load(file)
        return jsonify(memories)
    except FileNotFoundError:
        return jsonify({"error": "Memory file not found."}), 404

@app.route('/sms', methods=['POST'])
def sms_reply():
    sms = MessagingResponse()
    message_sender = request.values.get('From', None)
    message_body = request.values.get('Body', None)

    if message_sender != MY_PHONE and message_sender != "+13092590233":
        sms.message("You are not authorized, message Nico for access.")
        return str(sms)

    context.append({"role": "user", "content": message_body})
    response = get_response(context)
    response_with_emoji = "🍌📞:" + response
    sms.message(response_with_emoji)
    return str(sms)

@app.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json['user_input']
    if user_input is not None and user_input.strip() != "":
        assistant_response, skill_logs = assistant.get_response(user_input.strip())
        formatted_response = speak((assistant_response, skill_logs), config["assistant_name"])
        return jsonify(formatted_response)
    else:
        return jsonify({'text': '', 'additional_output': ''}), 400

@app.route('/get_news_feed')
def get_news_feed():
    feed_url = 'https://www.nasa.gov/rss/dyn/breaking_news.rss'  # You can change this to any RSS feed
    feed = feedparser.parse(feed_url)
    news_items = []
    for entry in feed.entries[:10]:  # Limit to 10 items
        news_items.append({
            'title': entry.title,
            'link': entry.link,
            'summary': entry.summary
        })
    return jsonify(news_items)

@app.route('/save_chat', methods=['POST'])
def save_chat():
    chat_messages = request.json.get('chatMessages', [])
    with open('chat_messages.json', 'w') as file:
        json.dump(chat_messages, file)
    return jsonify(success=True)

@app.route('/save_html_output', methods=['POST'])
def save_html_output():
    html_output = request.json.get('htmlOutput', '')
    with open('html_output.txt', 'w') as file:
        file.write(html_output)
    return jsonify(success=True)

@app.route('/save_skill_logs', methods=['POST'])
def save_skill_logs():
    skill_logs = request.json.get('skillLogs', [])
    with open('skill_logs.json', 'w') as file:
        json.dump(skill_logs, file)
    return jsonify(success=True)

@app.route('/upload_conversation_log', methods=['POST'])
def upload_conversation_log():
    if 'conversation_log' not in request.files:
        return jsonify(error='No file selected'), 400
    file = request.files['conversation_log']
    if file.filename == '':
        return jsonify(error='No file selected'), 400
    if file and file.filename.endswith('.html'):
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        file.save(file_path)
        with open(file_path, 'r') as f:
            conversation_log = f.read()
            update_ai_context(conversation_log)
        return jsonify(success=True)
    else:
        return jsonify(error='Invalid file type'), 400

def update_ai_context(conversation_log):
    # Parse the HTML conversation log and extract relevant information
    # Update the AI's context based on the extracted information
    # This is a placeholder function - you'll need to implement the actual logic
    print(f"Updating AI context with conversation log: {conversation_log[:100]}...")  # Print first 100 chars for debugging
    # TODO: Implement context updating logic

if __name__ == '__main__':
   app.run(debug=True)