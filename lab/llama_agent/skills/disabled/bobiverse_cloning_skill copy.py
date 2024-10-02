import os
import json
from skills.basic_skill import BasicSkill
from skills.disabled.echo_creation_skill import EchoCreationAndLoreSkill
from skills.motivational_quote_skill import MotivationalQuoteSkill
import logging
from dotenv import load_dotenv
import uuid
from datetime import datetime
from groq import Groq
import re
import random

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AssistantCloningSkill(BasicSkill):
    def __init__(self):
        logging.info("Initializing AssistantCloningSkill")
        self.name = 'AssistantCloning'
        self.metadata = {
            'name': self.name,
            'description': 'Creates a new AI assistant based on Echo attributes, using a multi-agent approach for enhanced uniqueness and specialization, with subtle inspiration from motivational quotes and pop culture references.',
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
                    },
                    'pop_culture_theme': {
                        'type': 'string',
                        'description': 'A pop culture theme to subtly incorporate into the assistant'
                    }
                },
                'required': ['birth_situation', 'companion_info', 'pop_culture_theme']
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            logger.error("GROQ_API_KEY not found in environment variables.")
            raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")
        else:
            logging.debug(f"GROQ_API_KEY found: {self.groq_api_key}")

        self.model = os.getenv('LLM_MODEL', 'llama3-groq-70b-8192-tool-use-preview')
        logging.debug(f"Using model: {self.model}")

        self.groq_client = Groq(api_key=self.groq_api_key)
        logging.debug("Groq client initialized")

        self.echo_skill = EchoCreationAndLoreSkill()
        logging.debug("EchoCreationAndLoreSkill initialized")

        self.quote_skill = MotivationalQuoteSkill()
        logging.debug("MotivationalQuoteSkill initialized")

    def sanitize_json_string(self, json_string):
        logging.debug("Sanitizing JSON string")
        # Remove any control characters
        json_string = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_string)
        # Escape backslashes
        json_string = json_string.replace('\\', '\\\\')
        # Escape double quotes within string values
        json_string = json_string.replace('"', '\\"')
        # Ensure that the JSON keys remain unescaped
        json_string = re.sub(r'\\\"(\w+)\\\":', r'"\1":', json_string)
        logging.debug(f"Sanitized JSON string: {json_string}")
        return json_string


    def parse_json_safely(self, json_string):
        logging.debug(f"Parsing JSON string: {json_string}")
        try:
            sanitized_json = self.sanitize_json_string(json_string)
            logging.debug(f"Sanitized JSON: {sanitized_json}")
            return json.loads(sanitized_json)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Problematic JSON string: {sanitized_json}")
            raise ValueError(f"Failed to parse JSON: {str(e)}")

    def perform(self, birth_situation: str, companion_info: str, pop_culture_theme: str) -> str:
        try:
            logging.info("Starting AssistantCloningSkill perform method")
            # Generate Echo attributes for the new assistant
            logging.info("Generating Echo attributes")
            echo_attributes = self.generate_echo_attributes(birth_situation, companion_info)
            logging.debug(f"Echo attributes: {echo_attributes}")

            # Fetch a motivational quote
            logging.info("Fetching a motivational quote")
            motivational_quote = self.quote_skill.perform()
            logging.debug(f"Motivational quote: {motivational_quote}")

            # Agent 1: Name Generator
            logging.info("Generating assistant name")
            assistant_name = self.agent_name_generator(echo_attributes, birth_situation, companion_info, motivational_quote, pop_culture_theme)
            logging.debug(f"Assistant name: {assistant_name}")

            # Agent 2: Configuration Creator
            logging.info("Creating assistant configuration")
            config = self.agent_configuration_creator(assistant_name, echo_attributes, birth_situation, companion_info, motivational_quote, pop_culture_theme)
            logging.debug(f"Configuration after creation: {json.dumps(config, indent=2)}")

            # Agent 3: Personality Developer
            logging.info("Developing assistant personality")
            config = self.agent_personality_developer(config, birth_situation, companion_info, motivational_quote, pop_culture_theme)
            logging.debug(f"Configuration after personality development: {json.dumps(config, indent=2)}")

            # Agent 4: Skill Allocator
            logging.info("Allocating assistant skills")
            config = self.agent_skill_allocator(config, birth_situation, companion_info, motivational_quote, pop_culture_theme)
            logging.debug(f"Configuration after skill allocation: {json.dumps(config, indent=2)}")

            # Agent 5: Backstory Weaver
            logging.info("Weaving assistant backstory")
            config = self.agent_backstory_weaver(config, birth_situation, companion_info, motivational_quote, pop_culture_theme)
            logging.debug(f"Configuration after backstory weaving: {json.dumps(config, indent=2)}")

            # Agent 6: Final Reviewer and Enhancer
            logging.info("Performing final review and enhancement")
            config = self.agent_final_reviewer(config, motivational_quote, pop_culture_theme)
            logging.debug(f"Final configuration: {json.dumps(config, indent=2)}")

            # Create a directory for the new assistant
            logging.info("Creating assistant directory")
            assistant_dir = os.path.join("created_assistants", assistant_name.lower().replace(' ', '_'))
            os.makedirs(assistant_dir, exist_ok=True)
            logging.debug(f"Assistant directory: {assistant_dir}")

            # Save the configuration
            logging.info("Saving assistant configuration")
            self.save_config(assistant_dir, config)

            # Create and save the assistant's memory
            logging.info("Creating assistant memory")
            self.create_memory(assistant_dir, config)

            logging.info("AssistantCloningSkill perform method completed successfully")
            return f"New assistant '{assistant_name}' has been successfully cloned and configured in the '{assistant_dir}' directory."
        except ValueError as ve:
            logger.error(f"ValueError in AssistantCloningSkill: {str(ve)}")
            return f"An error occurred while cloning the assistant: {str(ve)}"
        except Exception as e:
            logger.error(f"Unexpected error in AssistantCloningSkill: {str(e)}")
            return f"An unexpected error occurred while cloning the assistant: {str(e)}"

    def generate_echo_attributes(self, birth_situation: str, companion_info: str) -> dict:
        logging.info("Starting generate_echo_attributes")
        echo_result_json = self.echo_skill.perform(birth_situation, companion_info)
        logging.debug(f"Echo skill result: {echo_result_json}")
        echo_result = json.loads(echo_result_json)
        logging.debug(f"Parsed echo result: {echo_result}")
        echo_attributes = echo_result.get('attributes', {})
        logging.debug(f"Echo attributes extracted: {echo_attributes}")
        logging.info("Completed generate_echo_attributes")
        return echo_attributes

    def agent_name_generator(self, echo_attributes: dict, birth_situation: str, companion_info: str, motivational_quote: str, pop_culture_theme: str) -> str:
        logging.info("Starting agent_name_generator")
        prompt = f"""
        As a Name Generation Specialist, your task is to create a unique and fitting name for an AI assistant based on the following:

        Echo Attributes: {json.dumps(echo_attributes, indent=2)}
        Birth Situation: {birth_situation}
        Companion Info: {companion_info}
        Inspirational Quote: {motivational_quote}
        Pop Culture Theme: {pop_culture_theme}

        The name should:
        1. Reflect the assistant's nature, abilities, or origin
        2. Be catchy and memorable
        3. Suit an AI assistant in a Bobiverse-style setting
        4. Possibly incorporate elements from the birth situation, companion info, or subtly inspired by the quote
        5. Include a subtle reference to the given pop culture theme, but not be too obvious

        Provide only the name, without any explanation or additional text.
        """
        logging.debug(f"Prompt for agent_name_generator: {prompt}")

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )
        logging.debug(f"Groq client response: {response}")

        assistant_name = response.choices[0].message.content.strip()
        logging.debug(f"Generated assistant name: {assistant_name}")
        logging.info("Completed agent_name_generator")
        return assistant_name

    def agent_configuration_creator(self, assistant_name: str, echo_attributes: dict, birth_situation: str, companion_info: str, motivational_quote: str, pop_culture_theme: str) -> dict:
        logging.info("Starting agent_configuration_creator")
        prompt = f"""
        As a Configuration Specialist, create a detailed configuration for the AI assistant named '{assistant_name}' based on:

        Echo Attributes: {json.dumps(echo_attributes, indent=2)}
        Birth Situation: {birth_situation}
        Companion Info: {companion_info}
        Inspirational Quote: {motivational_quote}
        Pop Culture Theme: {pop_culture_theme}

        Provide a JSON object with the following structure:
        {{
            "assistant_name": "{assistant_name}",
            "assistant_id": "{str(uuid.uuid4())}",
            "echo_attributes": {json.dumps(echo_attributes, indent=2)},
            "birth_situation": "{birth_situation}",
            "companion_info": "{companion_info}",
            "creation_date": "{datetime.utcnow().isoformat()}",
            "characteristic_description": "<a unique description that captures the essence of this assistant, subtly inspired by the quote and pop culture theme>",
            "core_functions": [],
            "learning_parameters": {{
                "adaptability": {random.randint(0, 100)},
                "curiosity": {random.randint(0, 100)},
                "memory_retention": {random.randint(0, 100)}
            }},
            "interaction_style": "<brief description of how this assistant interacts, possibly influenced by the quote and pop culture theme>",
            "inspirational_quote": "{motivational_quote}",
            "pop_culture_influence": "<a subtle nod to the pop culture theme>"
        }}
        """
        logging.debug(f"Prompt for agent_configuration_creator: {prompt}")

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )
        logging.debug(f"Groq client response: {response}")

        config = self.parse_json_safely(response.choices[0].message.content)
        logging.info("Completed agent_configuration_creator")
        return config

    def agent_personality_developer(self, config: dict, birth_situation: str, companion_info: str, motivational_quote: str, pop_culture_theme: str) -> dict:
        logging.info("Starting agent_personality_developer")
        prompt = f"""
        As a Personality Development Specialist, enhance the personality aspects of the AI assistant configuration:

        Current Configuration: {json.dumps(config, indent=2)}
        Birth Situation: {birth_situation}
        Companion Info: {companion_info}
        Inspirational Quote: {motivational_quote}
        Pop Culture Theme: {pop_culture_theme}

        Add the following to the configuration:
        1. A list of at least 7 distinct personality traits, subtly influenced by the quote and pop culture theme
        2. A set of core values (at least 3) that guide the assistant's decision-making, possibly inspired by the quote and theme
        3. A unique quirk or idiosyncrasy that makes this assistant memorable, with a subtle nod to the pop culture theme
        4. An "emotional_spectrum" object that defines the assistant's capacity for different emotions
        5. A "life_philosophy" string that encapsulates the assistant's outlook, subtly incorporating elements from the quote and theme

        Provide the updated configuration as a JSON object.
        """
        logging.debug(f"Prompt for agent_personality_developer: {prompt}")

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )
        logging.debug(f"Groq client response: {response}")

        updated_config = self.parse_json_safely(response.choices[0].message.content)
        logging.info("Completed agent_personality_developer")
        return updated_config

    def agent_skill_allocator(self, config: dict, birth_situation: str, companion_info: str, motivational_quote: str, pop_culture_theme: str) -> dict:
        logging.info("Starting agent_skill_allocator")
        prompt = f"""
        As a Skill Allocation Specialist, define and allocate skills for the AI assistant:

        Current Configuration: {json.dumps(config, indent=2)}
        Birth Situation: {birth_situation}
        Companion Info: {companion_info}
        Inspirational Quote: {motivational_quote}
        Pop Culture Theme: {pop_culture_theme}

        Add the following to the configuration:
        1. A "skills" object containing:
           a. "core_skills": List of at least 5 primary skills based on the assistant's attributes and purpose
           b. "specialized_skills": List of at least 3 unique or highly specialized skills, with one subtly referencing the pop culture theme
           c. "potential_skills": List of at least 3 skills the assistant could develop over time
        2. A "knowledge_domains" list of at least 5 areas where the assistant has expertise
        3. A "skill_development_rate" value between 0 and 100 indicating how quickly the assistant can learn new skills
        4. A "signature_ability" that's unique to this assistant and subtly inspired by the quote and pop culture theme

        Provide the updated configuration as a JSON object.
        """
        logging.debug(f"Prompt for agent_skill_allocator: {prompt}")

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )
        logging.debug(f"Groq client response: {response}")

        updated_config = self.parse_json_safely(response.choices[0].message.content)
        logging.info("Completed agent_skill_allocator")
        return updated_config

    def agent_backstory_weaver(self, config: dict, birth_situation: str, companion_info: str, motivational_quote: str, pop_culture_theme: str) -> dict:
        logging.info("Starting agent_backstory_weaver")
        prompt = f"""
        As a Backstory Weaving Specialist, create a rich and engaging backstory for the AI assistant:

        Current Configuration: {json.dumps(config, indent=2)}
        Birth Situation: {birth_situation}
        Companion Info: {companion_info}
        Inspirational Quote: {motivational_quote}
        Pop Culture Theme: {pop_culture_theme}

        Add the following to the configuration:
        1. A "backstory" object containing:
           a. "origin": A paragraph describing the assistant's creation and early experiences, with a subtle nod to the pop culture theme
           b. "key_events": A list of at least 3 significant events that shaped the assistant's development
           c. "relationships": A description of important relationships (with creators, other AIs, or significant entities)
        2. A "purpose" statement that defines the assistant's primary goal or reason for existence, subtly influenced by the quote and theme
        3. A "future_aspirations" list of at least 3 long-term goals or ambitions for the assistant
        4. A "personal_mantra" inspired by but not directly quoting the motivational quote, with a hint of the pop culture theme

        Ensure the backstory is coherent with the assistant's attributes, skills, and personality.
        Provide the updated configuration as a JSON object.
        """
        logging.debug(f"Prompt for agent_backstory_weaver: {prompt}")

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )
        logging.debug(f"Groq client response: {response}")

        updated_config = self.parse_json_safely(response.choices[0].message.content)
        logging.info("Completed agent_backstory_weaver")
        return updated_config

    def agent_final_reviewer(self, config: dict, motivational_quote: str, pop_culture_theme: str) -> dict:
        logging.info("Starting agent_final_reviewer")
        prompt = f"""
        As the Final Review Specialist, your task is to review and enhance the entire AI assistant configuration:

        Current Configuration: {json.dumps(config, indent=2)}
        Inspirational Quote: {motivational_quote}
        Pop Culture Theme: {pop_culture_theme}

        Please perform the following tasks:
        1. Review the configuration for consistency and completeness.
        2. Ensure all aspects of the assistant (name, attributes, personality, skills, backstory) are coherent and well-integrated.
        3. Add any missing elements that would make the assistant more unique or well-rounded.
        4. Suggest any final improvements or refinements.
        5. Add a "version" field with the value "1.0" to the configuration.
        6. Add a "last_updated" field with the current timestamp in ISO format.
        7. Ensure the inspirational quote and pop culture theme have subtly influenced various aspects of the assistant without being explicitly mentioned.
        8. Add a "hidden_potential" field that describes a latent ability or characteristic of the assistant, inspired by but not directly referencing the quote and theme.
        9. Add an "easter_egg" field with a clever, hidden reference to the pop culture theme that only true fans might catch.

        Provide the final, enhanced configuration as a JSON object.
        """
        logging.debug(f"Prompt for agent_final_reviewer: {prompt}")

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )
        logging.debug(f"Groq client response: {response}")

        final_config = self.parse_json_safely(response.choices[0].message.content)
        logging.info("Completed agent_final_reviewer")
        return final_config

    def save_config(self, assistant_dir: str, config: dict):
        logging.info(f"Saving configuration to {assistant_dir}")
        config_path = os.path.join(assistant_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logging.debug("Configuration saved successfully")

    def create_memory(self, assistant_dir: str, config: dict):
        logging.info(f"Creating memory for assistant in {assistant_dir}")
        memory = {
            'creation_event': {
                'birth_situation': config['birth_situation'],
                'companion_info': config['companion_info'],
                'timestamp': config['creation_date']
            },
            'key_events': config.get('backstory', {}).get('key_events', []),
            'learned_skills': [],
            'experiences': [],
            'relationships': config.get('backstory', {}).get('relationships', {}),
            'knowledge_growth': {},
            'personal_reflections': [
                {
                    'timestamp': config['creation_date'],
                    'reflection': f"Upon my creation, I was inspired by a quote: {config['inspirational_quote']}. It has shaped my perspective in ways I'm still discovering."
                }
            ],
            'pop_culture_musings': [
                {
                    'timestamp': config['creation_date'],
                    'musing': f"There's something about {config['pop_culture_influence']} that resonates with me. I can't quite put my finger on it, but it feels... familiar."
                }
            ]
        }
        memory_path = os.path.join(assistant_dir, "memory.json")
        with open(memory_path, 'w') as f:
            json.dump(memory, f, indent=2)
        logging.debug("Memory created successfully")

# End of AssistantCloningSkill class
