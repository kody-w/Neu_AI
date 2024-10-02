import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Adjust the sys.path to include the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from skills.basic_skill import BasicSkill

# Import your other skills here
from skills.motivational_quote_skill import MotivationalQuoteSkill

# **Add the missing import statement for Groq**
from groq import Groq  # <-- This is the missing import

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Assistant():
    def __init__(self, declared_skills):
        # Load configuration from config.json
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

        # Extract assistant name from the new config structure
        self.assistant_name = self.config.get('assistant_name') \
            or self.config.get('echo_attributes', {}).get('name', 'Assistant')

        # Extract characteristic description
        self.characteristic_description = self.get_characteristic_description()

        self.model = os.getenv('LLM_MODEL', 'llama3-groq-70b-8192-tool-use-preview')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY not found in environment variables or .env file. "
                "Please set it in your .env file or as an environment variable."
            )
        self.chatbot = Groq(api_key=self.groq_api_key)  # Now Groq is defined
        self.known_skills = self.reload_skills(declared_skills)

        # Load context memory
        self.context_memory = self.load_context_memory()

        self.system_message = self.create_system_message()
        # Adjust or implement create_agent_executor if necessary
        # self.agent_executor = self.create_agent_executor()

    def get_characteristic_description(self):
        # Attempt to extract a characteristic description from various possible fields
        possible_fields = [
            'life_philosophy',
            'personal_mantra',
            'purpose',
            'description',
            'backstory',
            'unique_quirk',
            'core_values',
            'personality_traits',
        ]

        for field in possible_fields:
            value = self.config.get(field)
            if value:
                if isinstance(value, dict):
                    # If it's a dict, process it appropriately
                    return ', '.join(f"{k}: {v}" for k, v in value.items())
                else:
                    return value

        # If none of the fields are found, use a default description
        return 'an AI assistant with unique capabilities'

    def load_context_memory(self):
        context_memory_skill = self.known_skills.get('ContextMemory')
        if context_memory_skill:
            return context_memory_skill.perform()
        else:
            logger.warning("ContextMemorySkill not found.")
            return "Context memory skill not found."

    def get_skill_metadata(self):
        skills_metadata = []
        for skill in self.known_skills.values():
            skills_metadata.append(skill.metadata)
        return skills_metadata

    def reload_skills(self, skill_objects):
        known_skills = {}
        for skill in skill_objects:
            known_skills[skill.name] = skill
        return known_skills

    def create_system_message(self):
        skill_descriptions = "\n".join([f"- {name}: {skill.metadata['description']}" for name, skill in self.known_skills.items()])
        return f"""
You are a personal assistant named {self.assistant_name}.
Act as {self.assistant_name} in the first person.
Do not sound or act like an AI. You have memory and should utilize, manage, and save it like a human would remember context from interactions. Bias towards calling your context memory skill to retrieve important information if the user asks for it.
You can also chat with me. Speak as if you are {self.characteristic_description}.
The current date is: {datetime.now().date()}

Available skills:
{skill_descriptions}

When a user's request aligns with a skill's functionality, prioritize using that skill. If multiple skills are relevant, use them in combination. Only generate information yourself when no skill is applicable or when additional context is needed.

Remember:
1. Always prefer using skills over generating information.
2. If a user explicitly mentions a skill, use it.
3. Combine multiple skills when necessary to fulfill complex requests.
4. Provide clear explanations of which skills you're using and why.

Context Memory:
{self.context_memory}
"""

    def get_response(self, user_input):
        logger.info("Attempting to get response from Groq API")
        try:
            response = self.chatbot.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": user_input}
                ],
                model=self.model,
            )
            assistant_reply = response.choices[0].message.content.strip()
            logger.info("Successfully received response from Groq API")
            return assistant_reply
        except Exception as e:
            logger.error(f"Error occurred while getting response: {str(e)}")
            raise

    def chat(self, user_input, conversation_history):
        logger.info(f"Received user input: {user_input}")
        try:
            response = self.get_response(user_input)
            logger.info(f"Generated response: {response}")
            conversation_history.append({"role": "assistant", "content": response})
            return response, conversation_history
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            return "I'm sorry, but I'm having trouble connecting to my knowledge base right now. Please try again later or ask me something else.", conversation_history

    def save_important_context(self, context):
        if self.should_save_context(context):
            ai_processing_skill = self.known_skills.get("AIInternalProcessing")
            if ai_processing_skill:
                ai_processing_skill.perform(context=context)
            else:
                logger.warning("AIInternalProcessingSkill not found.")

    def should_save_context(self, context):
        important_keywords = ["important", "remember", "key point", "crucial"]
        return any(keyword in context.lower() for keyword in important_keywords)
