import json
import sys
import os
import importlib
import inspect
import re
from termcolor import colored, cprint
from assistant import Assistant
from skills.basic_skill import BasicSkill
import streamlit as st
from dotenv import load_dotenv
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def load_skills_from_folder():
    skills_directory = os.path.abspath("./skills")
    skill_files = []
    for root, dirs, files in os.walk(skills_directory):
        for file in files:
            if file.endswith(".py") and file != "__init__.py" and file != "basic_skill.py":
                full_path = os.path.join(root, file)
                skill_files.append(full_path)

    declared_skills = []
    for skill_file in skill_files:
        # Compute the module name relative to the skills directory
        rel_path = os.path.relpath(skill_file, skills_directory)
        module_name = os.path.splitext(rel_path)[0].replace(os.sep, '.')
        # Prepend 'skills' to the module name
        full_module_name = 'skills.' + module_name
        module = importlib.import_module(full_module_name)
        for name, member in inspect.getmembers(module):
            if inspect.isclass(member) and issubclass(member, BasicSkill) and member is not BasicSkill:
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

def cli_chat(assistant):
    print(f"Welcome to {assistant.assistant_name}. Type 'exit' to end the conversation.")
    conversation_history = []

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        try:
            response, conversation_history = assistant.chat(user_input, conversation_history)
            print(f"{assistant.assistant_name}: {response}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Error details:")
            print(traceback.format_exc())
            print("Please try again or type 'exit' to quit.")

def streamlit_chat():
    st.title("AI Assistant")

    # Initialize assistant
    if "assistant" not in st.session_state:
        try:
            st.session_state.assistant = Assistant(load_skills_from_folder())
        except Exception as e:
            st.error(f"Error initializing the assistant: {str(e)}")
            st.error("Error details:")
            st.error(traceback.format_exc())
            return

    # Initialize chat history
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    # Display chat messages from history on app rerun
    for message in st.session_state.conversation_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What would you like to do today?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)

        # Get AI response
        try:
            response, st.session_state.conversation_history = st.session_state.assistant.chat(
                prompt, st.session_state.conversation_history
            )
            st.chat_message("assistant").markdown(response)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Error details:")
            st.error(traceback.format_exc())

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        try:
            assistant = Assistant(load_skills_from_folder())
            cli_chat(assistant)
        except Exception as e:
            print(f"Error initializing the assistant: {str(e)}")
            print("Error details:")
            print(traceback.format_exc())
            print("Please check your .env file or set the required environment variables and try again.")
    else:
        streamlit_chat()
