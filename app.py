from flask import Flask, request, render_template, jsonify, redirect, url_for, Response, send_file
from twilio.twiml.messaging_response import MessagingResponse
from config.settings import MY_PHONE
import json
import feedparser
import requests
from bs4 import BeautifulSoup
import os
from assistant import Assistant
from skills.basic_skill import BasicSkill
import importlib
import inspect
from werkzeug.utils import secure_filename
import csv
import pandas as pd

app = Flask(__name__)
app.static_folder = 'static'


# Load assistant configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Directory for saving webpages
SAVE_DIR = 'saved_webpages'

# Define the list of prompts for dynamically generated buttons
prompts = [    
    {
        "button_text": "🤖🤝",
        "prompt": "Retrieve the latest updates from Dynamics 365 on key opportunities on customer engagements. then output to the webview a summary of the key insights and trends that you have observed in the data and what we should prioritize and focus on next."
    },
    {
        "button_text": "🤖🔮",
        "prompt": "What do you remember from your long term memory from a business perspective? Output to the webview a summary as if you were getting someone up to speed at a high crash course level. what should be my next steps. Develop an action plan. output to webview"
    },
    {
        "button_text": "🤖🤖",
        "prompt": "Provide a numbered list of the next three next best prompts using your current situation for the user to use next. These prompts should be written from the user's first person perspective so they dont have to change anything to use them. then output to the webview as clickable buttons. Make the buttons copy the prompt text to the clipboard for the user to use when they are clicked. Always add the the prompts to output to webview"
    },
    {
        "button_text": "🤖🔍",
        "prompt": "I need to manage memory context for a recent conversation. Could you help? Give me the conversation details related to themes of business from your long term memory."
    },
    {
        "button_text": "🤖📋",
        "prompt": "what should be my next steps? Develop an action plan from a business perspective. output to webview"
    },
    {
        "button_text": "🤖💭",
        "prompt": "Identify any patterns, trends, or recurring themes you've noticed in our conversations and offer your analysis or thoughts on them from a business point of view. Ouput to the webview a summary of your findings and insights and what we should do next in relation to them."
    },
    {
        "button_text": "🤖💾",
        "prompt": "Save the details of this conversations to your long term memory. Output to the webview a summary of the key details that you have saved. The user will depend on these memories to get up to speed on the conversation through what you have saved so the details are importnat like action items and key specifics and insights and next steps along with anything else that would be relelvent to being an on top of it executive assistant if you were to solely rely on your memory."
    }
]

# Modify dynamic content store to use the assistant's name from config and include prompt buttons
prompt_buttons = ""
for prompt in prompts:
    prompt_buttons += f'<button class="btn example-btn" data-example="{prompt["prompt"]}" title="{prompt["prompt"]}">{prompt["button_text"]}</button>'

dynamic_content_store = f''''''

# Hardcoded schedules for demonstration purposes
schedules = {
    'John': {
        '2023-06-05': ['10:00', '14:00'],
        '2023-06-06': ['11:00', '15:00'],
        '2023-06-07': ['09:00', '13:00'],
        '2023-06-08': ['14:00', '17:00'],
        '2023-06-09': ['10:00', '12:00']
    },
    'Sarah': {
        '2023-06-05': ['11:00', '16:00'],
        '2023-06-06': ['09:00', '12:00'],
        '2023-06-07': ['14:00', '17:00'],
        '2023-06-08': ['10:00', '13:00'],
        '2023-06-09': ['11:00', '15:00']
    }
}


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


def load_skills():
    try:
        with open('skills.json', 'r') as file:
            skills = json.load(file)
    except FileNotFoundError:
        skills = []
    return skills


def save_skills(skills):
    with open('skills.json', 'w') as file:
        json.dump(skills, file, indent=2)


@app.route('/')
def index():
    try:
        with open('memory.json', 'r') as memory_file:
            memories = json.load(memory_file)
    except FileNotFoundError:
        memories = {'error': 'Memory file not found.'}

    feed_url = request.args.get(
        'feed_url', 'https://www.nasa.gov/rss/dyn/breaking_news.rss')
    if request.method == 'POST':
        if 'feed_url' in request.form and request.form['feed_url']:
            feed_url = request.form['feed_url']
            return redirect(url_for('index', feed_url=feed_url))
        elif 'save_links' in request.form:
            feed = feedparser.parse(feed_url)
            save_links(feed)
            return render_template('index.html', feed=feed, feed_url=feed_url, memories=memories, message='Links saved successfully.', assistant=assistant, assistant_name=config["assistant_name"], prompts=prompts)
    feed = feedparser.parse(feed_url)
    return render_template('index.html', feed=feed, feed_url=feed_url, memories=memories, assistant=assistant, assistant_name=config["assistant_name"], prompts=prompts)


@app.route('/skills', methods=['GET'])
def get_skills():
    skills = load_skills()
    return jsonify(skills)


@app.route('/skills', methods=['POST'])
def create_skill():
    skill_data = request.json
    skills = load_skills()
    skill_id = len(skills) + 1
    skill_data['id'] = skill_id
    skill_data['upvotes'] = 0
    skill_data['downvotes'] = 0
    skill_data['reviews'] = []
    skill_data['usage_count'] = 0
    skill_data['rating'] = 0
    skill_data['version'] = '1.0'
    skills.append(skill_data)
    save_skills(skills)
    return jsonify({'message': 'Skill created successfully'})


@app.route('/skills/<int:skill_id>/vote', methods=['POST'])
def vote_skill(skill_id):
    vote_type = request.json['type']
    skills = load_skills()
    skill = next((skill for skill in skills if skill['id'] == skill_id), None)
    if skill:
        if vote_type == 'upvote':
            skill['upvotes'] += 1
        elif vote_type == 'downvote':
            skill['downvotes'] += 1
        save_skills(skills)
        return jsonify({'message': 'Vote recorded successfully'})
    else:
        return jsonify({'error': 'Skill not found'}), 404


@app.route('/skills/<int:skill_id>/review', methods=['POST'])
def add_review(skill_id):
    review_text = request.json['review']
    skills = load_skills()
    skill = next((skill for skill in skills if skill['id'] == skill_id), None)
    if skill:
        skill['reviews'].append(review_text)
        save_skills(skills)
        return jsonify({'message': 'Review added successfully'})
    else:
        return jsonify({'error': 'Skill not found'}), 404


@app.route('/skills/<int:skill_id>/usage', methods=['POST'])
def increment_usage_count(skill_id):
    skills = load_skills()
    skill = next((skill for skill in skills if skill['id'] == skill_id), None)
    if skill:
        skill['usage_count'] += 1
        save_skills(skills)
        return jsonify({'message': 'Usage count incremented successfully'})
    else:
        return jsonify({'error': 'Skill not found'}), 404


@app.route('/skills/<int:skill_id>/rate', methods=['POST'])
def rate_skill(skill_id):
    rating = request.json['rating']
    skills = load_skills()
    skill = next((skill for skill in skills if skill['id'] == skill_id), None)
    if skill:
        skill['rating'] = rating
        save_skills(skills)
        return jsonify({'message': 'Skill rated successfully'})
    else:
        return jsonify({'error': 'Skill not found'}), 404


@app.route('/insert_content', methods=['POST'])
def insert_content():
    global dynamic_content_store
    data = request.get_json()
    dynamic_content_store = data.get('html_content', '')
    return jsonify(success=True), 200


@app.route('/get_dynamic_content')
def get_dynamic_content():
    return dynamic_content_store


@app.route('/load_memories', methods=['GET'])
def load_memories():
    search_query = request.args.get('search', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sort_by = request.args.get('sort_by', 'date')
    tags = request.args.get('tags', '').split(',')
    page = int(request.args.get('page', 1))
    page_size = 10

    try:
        with open('memory.json', 'r') as file:
            memories = json.load(file)

        filtered_memories = []
        for memory in memories.values():
            if search_query.lower() in memory['message'].lower() and \
               (not start_date or memory['date'] >= start_date) and \
               (not end_date or memory['date'] <= end_date) and \
               (not tags or any(tag.lower() in memory['theme'].lower() for tag in tags)):
                # Use username as the memory ID
                memory['id'] = memory['username']
                filtered_memories.append(memory)

        sorted_memories = sorted(
            filtered_memories, key=lambda x: x[sort_by], reverse=True)

        total_memories = len(sorted_memories)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_memories = sorted_memories[start_index:end_index]

        return jsonify({
            'memories': paginated_memories,
            'total_memories': total_memories,
            'current_page': page
        })
    except FileNotFoundError:
        return jsonify({"error": "Memory file not found."}), 404


@app.route('/load_memory_details', methods=['GET'])
def load_memory_details():
    memory_id = request.args.get('memory_id', '')

    try:
        with open('memory.json', 'r') as file:
            memories = json.load(file)

        for memory in memories.values():
            if memory['username'] == memory_id:
                return jsonify(memory)

        return jsonify({"error": "Memory not found."}), 404
    except FileNotFoundError:
        return jsonify({"error": "Memory file not found."}), 404


@app.route('/export_memories', methods=['GET'])
def export_memories():
    search_query = request.args.get('search', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sort_by = request.args.get('sort_by', 'date')
    tags = request.args.get('tags', '').split(',')

    try:
        with open('memory.json', 'r') as file:
            memories = json.load(file)

        filtered_memories = []
        for memory in memories.values():
            if search_query.lower() in memory['message'].lower() and \
               (not start_date or memory['date'] >= start_date) and \
               (not end_date or memory['date'] <= end_date) and \
               (not tags or any(tag.lower() in memory['theme'].lower() for tag in tags)):
                filtered_memories.append(memory)

        sorted_memories = sorted(
            filtered_memories, key=lambda x: x[sort_by], reverse=True)

        csv_data = [['Username', 'Message', 'Mood', 'Theme', 'Date', 'Time']]
        for memory in sorted_memories:
            csv_data.append([
                memory['username'],
                memory['message'],
                memory['mood'],
                memory['theme'],
                memory['date'],
                memory['time']
            ])

        csv_file = 'memories.csv'
        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(csv_data)

        return send_file(csv_file, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "Memory file not found."}), 404


@app.route('/sms', methods=['GET', 'POST'])
def sms_reply():
    # Create a new message response
    sms = MessagingResponse()

    # Get the sender phone number and the message body
    message_sender = request.values.get('From', None)
    message_body = request.values.get('Body', None)

    # Check if the sender is authorized
    if message_sender != MY_PHONE and message_sender != "+13092590233":
        sms.message("You are not authorized, message Nico for access.")
        return str(sms)

    # Update context with the user's message
    if message_body is not None and message_body.strip() != "":
        context.append({"role": "user", "content": message_body.strip()})

    # Get a response based on the updated context
    response = get_response(context)

    # Add the banana phone emoji to the response
    response_with_emoji = """
    """ + "🍌📞:" + response + ""

    # Add the response with the emoji to the message and return it
    sms.message(response_with_emoji)
    return str(sms)


@app.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json['user_input']
    if user_input is not None and user_input.strip() != "":
        assistant_response, skill_logs = assistant.get_response(user_input.strip())
        return jsonify({'response': assistant_response, 'skill_logs': skill_logs})
    else:
        return jsonify({'response': '', 'skill_logs': ''}), 400


@app.route('/schedule_meeting', methods=['POST'])
def schedule_meeting():
   meeting_details = request.json
   participants = meeting_details['participants']
   date_range = meeting_details['date_range']
   duration = meeting_details['duration']
   purpose = meeting_details['purpose']
   # Check availability of participants
   available_slots = []
   start_date, end_date = date_range.split(' - ')
   current_date = start_date
   while current_date <= end_date:
       available_slot = True
       for participant in participants:
           if participant in schedules:
               if current_date in schedules[participant]:
                   available_slot = False
                   break
       if available_slot:
           available_slots.append(current_date)
       current_date = (pd.to_datetime(current_date) +
                       pd.Timedelta(days=1)).strftime('%Y-%m-%d')

   if available_slots:
       selected_date = available_slots[0]
       return jsonify({'message': f'Meeting scheduled successfully on {selected_date}!'})
   else:
       return jsonify({'message': 'No available slots found for the specified participants and date range.'})


def save_links(feed):
   """Function to save feed links as HTML."""
   if not os.path.exists(SAVE_DIR):
       os.makedirs(SAVE_DIR)
   for entry in feed.entries:
       url = entry.link
       try:
           response = requests.get(url)
           soup = BeautifulSoup(response.content, 'html.parser')
           filename = os.path.join(
               SAVE_DIR, entry.title.replace(' ', '_') + '.html')
           with open(filename, 'w', encoding='utf-8') as file:
               file.write(str(soup))
       except Exception as e:
           print(f"Failed to save {url}: {e}")


@app.route('/stream')
def stream():
   def event_stream():
       while True:
           user_input = request.args.get('message', '')
           assistant_response = assistant.get_response(user_input)
           for chunk in speak(assistant_response):
               yield chunk
   return Response(event_stream(), mimetype='text/event-stream')


@app.route('/save_chat', methods=['POST'])
def save_chat():
   chat_messages = request.json.get('chatMessages', [])

   # Save the chat messages to a JSON file
   with open('chat_messages.json', 'w') as file:
       json.dump(chat_messages, file)

   return jsonify(success=True)


@app.route('/save_html_output', methods=['POST'])
def save_html_output():
   html_output = request.json.get('htmlOutput', '')

   # Save the HTML output to a text file
   with open('html_output.txt', 'w') as file:
       file.write(html_output)

   return jsonify(success=True)


@app.route('/save_skill_logs', methods=['POST'])
def save_skill_logs():
   skill_logs = request.json.get('skillLogs', [])

   # Save the skill logs to a JSON file
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
   # ...
   print()


# @app.route('/get_art_files', methods=['GET'])
# def get_art_files():
#     art_dir = 'static/art/'  # Replace with the actual path to the 'art' directory
#     file_list = os.listdir(art_dir)
#     print(file_list)
#     return jsonify(file_list)

# Run the app if this script is the main one executed
if __name__ == '__main__':
   app.run(debug=True)
    