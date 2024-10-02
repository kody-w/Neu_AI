import os
import json
import shutil
from skills.basic_skill import BasicSkill
from skills.disabled.echo_creation_skill import EchoCreationAndLoreSkill
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import logging
from dotenv import load_dotenv
import uuid
from datetime import datetime
from groq import Groq

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AdvancedBobiverseEchoAssistantCloningSkill(BasicSkill):
    def __init__(self):
        self.name = 'AdvancedBobiverseEchoAssistantCloning'
        self.metadata = {
            'name': self.name,
            'description': 'An advanced skill to clone and customize assistants in a Bobiverse-style, utilizing the Echo creation process and agent-based validation and customization.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'birth_situation': {
                        'type': 'string',
                        'description': 'The situation where the new assistant is created'
                    },
                    'companion_info': {
                        'type': 'string',
                        'description': "Information about the new assistant's companion or creator"
                    }
                },
                'required': ['birth_situation', 'companion_info']
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")
        self.model = os.getenv('LLM_MODEL', 'llama3-groq-70b-8192-tool-use-preview')
        self.chatbot = ChatGroq(model=self.model, groq_api_key=self.groq_api_key)
        self.groq_client = Groq(api_key=self.groq_api_key)
        self.echo_skill = EchoCreationAndLoreSkill()

    def perform(self, birth_situation, companion_info):
        try:
            # Generate Echo attributes for the original assistant
            original_echo_attributes = self.generate_echo_attributes("Original AI research lab", "Created by pioneering AI researchers")
            original_assistant_name = self.generate_assistant_name(original_echo_attributes)

            # Create the original assistant if it doesn't exist
            original_assistant_dir = os.path.join("created_assistants", original_assistant_name.lower().replace(' ', '_'))
            if not os.path.exists(original_assistant_dir):
                os.makedirs(original_assistant_dir, exist_ok=True)
                original_config = self.create_original_config(original_assistant_name, original_echo_attributes)
                self.save_config(original_assistant_dir, original_config)
                self.create_original_memory(original_assistant_dir)
                logger.info(f"Created original assistant: {original_assistant_name}")

            # Generate Echo attributes for the new assistant
            new_echo_attributes = self.generate_echo_attributes(birth_situation, companion_info)
            new_assistant_name = self.generate_assistant_name(new_echo_attributes)

            # Create a directory for the new assistant
            new_assistant_dir = os.path.join("created_assistants", new_assistant_name.lower().replace(' ', '_'))
            os.makedirs(new_assistant_dir, exist_ok=True)

            # Copy the original assistant's files
            self.copy_assistant_files(original_assistant_dir, new_assistant_dir)

            # Load the original assistant's config and memory
            original_config = self.load_config(original_assistant_dir)
            original_memory = self.load_memory(original_assistant_dir)

            # Create the new assistant's configuration
            new_config = self.create_new_config(original_config, new_assistant_name, new_echo_attributes)

            # Agent-based validation and customization
            new_config = self.agent_based_customization(new_config, birth_situation, companion_info)

            # Save the new configuration
            self.save_config(new_assistant_dir, new_config)

            # Update the new assistant's memory
            self.update_memory(new_assistant_dir, original_memory, birth_situation, companion_info)

            return f"The {new_assistant_name} assistant has been successfully cloned from {original_assistant_name}, customized, and validated in the '{new_assistant_dir}' directory."
        except Exception as e:
            logger.error(f"An error occurred in AdvancedBobiverseEchoAssistantCloningSkill: {str(e)}")
            return f"An error occurred while cloning the assistant: {str(e)}"

    def generate_echo_attributes(self, birth_situation, companion_info):
        echo_result = json.loads(self.echo_skill.perform(birth_situation, companion_info))
        return echo_result['attributes']

    def generate_assistant_name(self, echo_attributes):
        prompt = f"""
        Generate a unique and fitting name for an AI assistant based on the following Echo attributes:
        {json.dumps(echo_attributes, indent=2)}

        The name should reflect the assistant's nature, abilities, or origin. It should be catchy and memorable, 
        suitable for an AI assistant in a Bobiverse-style setting.

        Provide only the name, without any explanation or additional text.
        """

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )

        return response.choices[0].message.content.strip()

    def create_original_config(self, assistant_name, echo_attributes):
        return {
            'assistant_name': assistant_name,
            'assistant_id': str(uuid.uuid4()),
            'echo_attributes': echo_attributes,
            'creation_date': datetime.now().isoformat(),
            'characteristic_description': 'A pioneering AI assistant with advanced capabilities',
            'personality_traits': ['Curious', 'Analytical', 'Helpful'],
            'base_skills': ['NaturalLanguageProcessing', 'DataAnalysis', 'ProblemSolving']
        }

    def create_original_memory(self, assistant_dir):
        memory = {
            'creation_event': {
                'birth_situation': "Original AI research lab",
                'companion_info': "Created by pioneering AI researchers",
                'timestamp': datetime.now().isoformat()
            }
        }
        memory_path = os.path.join(assistant_dir, "memory.json")
        with open(memory_path, 'w') as f:
            json.dump(memory, f, indent=2)

    def copy_assistant_files(self, src_dir, dst_dir):
        for item in os.listdir(src_dir):
            s = os.path.join(src_dir, item)
            d = os.path.join(dst_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks=False, ignore=None)
            else:
                shutil.copy2(s, d)

    def load_config(self, assistant_dir):
        config_path = os.path.join(assistant_dir, "config.json")
        with open(config_path, 'r') as f:
            return json.load(f)

    def load_memory(self, assistant_dir):
        memory_path = os.path.join(assistant_dir, "memory.json")
        if os.path.exists(memory_path):
            with open(memory_path, 'r') as f:
                return json.load(f)
        return {}

    def create_new_config(self, original_config, new_assistant_name, echo_attributes):
        new_config = original_config.copy()
        new_config.update({
            'assistant_name': new_assistant_name,
            'assistant_id': str(uuid.uuid4()),
            'echo_attributes': echo_attributes,
            'cloned_from': original_config['assistant_name'],
            'creation_date': datetime.now().isoformat()
        })
        return new_config

    def agent_based_customization(self, config, birth_situation, companion_info):
        prompt = f"""
        As an AI agent specializing in assistant customization and validation, your task is to review and enhance the configuration for a newly cloned AI assistant. 
        Consider the following:

        1. Birth Situation: {birth_situation}
        2. Companion Info: {companion_info}
        3. Current Configuration: {json.dumps(config, indent=2)}

        Please perform the following tasks:

        1. Validate the configuration for consistency and completeness.
        2. Suggest improvements or additions to make the assistant unique and well-suited to its birth situation and companion.
        3. Refine the 'characteristic_description' to better reflect the assistant's unique traits and origin.
        4. Ensure that the assistant's personality and abilities are consistent with its Echo attributes.
        5. Suggest any necessary modifications to the assistant's base skills to accommodate its unique features.

        Provide your response as a JSON object with the following structure:
        {{
            "validated_config": {{}}, // The validated and improved configuration
            "personality_traits": [], // A list of key personality traits for this assistant
            "base_skills": [], // A list of base skills for this assistant
            "validation_notes": "" // Any notes or explanations about your changes and suggestions
        }}
        """

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )

        result = json.loads(response.choices[0].message.content)

        # Update the configuration with the agent's suggestions
        config.update(result['validated_config'])
        config['personality_traits'] = result['personality_traits']
        config['base_skills'] = result['base_skills']
        config['validation_notes'] = result['validation_notes']

        return config

    def save_config(self, assistant_dir, config):
        config_path = os.path.join(assistant_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def update_memory(self, assistant_dir, original_memory, birth_situation, companion_info):
        memory_path = os.path.join(assistant_dir, "memory.json")
        new_memory = original_memory.copy()
        new_memory['cloning_event'] = {
            'birth_situation': birth_situation,
            'companion_info': companion_info,
            'timestamp': datetime.now().isoformat()
        }
        with open(memory_path, 'w') as f:
            json.dump(new_memory, f, indent=2)

# End of AdvancedBobiverseEchoAssistantCloningSkill class