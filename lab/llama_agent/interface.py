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
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

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

def cli_chat(assistant):
    print("Welcome to the AI Assistant. Type 'exit' to end the conversation.")
    messages = [SystemMessage(content=assistant.system_message)]
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        try:
            response, messages = assistant.chat(user_input, messages)
            print(f"AI: {response}")
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
    if "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content=st.session_state.assistant.system_message)
        ]

    # Display chat messages from history on app rerun
    for message in st.session_state.messages[1:]:  # Skip the system message
        with st.chat_message(message.type):
            st.markdown(message.content)

    # React to user input
    if prompt := st.chat_input("What would you like to do today?"):
        # Display user message in chat message container
        st.chat_message("human").markdown(prompt)

        # Get AI response
        with st.chat_message("ai"):
            try:
                response, st.session_state.messages = st.session_state.assistant.chat(prompt, st.session_state.messages)
                st.markdown(response)
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