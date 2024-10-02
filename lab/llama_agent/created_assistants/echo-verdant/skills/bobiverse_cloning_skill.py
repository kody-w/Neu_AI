import os
import json
import logging
import uuid
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from skills.basic_skill import BasicSkill
from skills.disabled.echo_creation_skill import EchoCreationAndLoreSkill
from skills.motivational_quote_skill import MotivationalQuoteSkill

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AssistantCloningSkill(BasicSkill):
    def __init__(self):
        self.name = 'AssistantCloning'
        self.metadata = {
            'name': self.name,
            'description': 'Creates a new AI assistant using a multi-agent approach for enhanced uniqueness and specialization.',
        }
        super().__init__(name=self.name, metadata=self.metadata)

        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")
        self.model = os.getenv('LLM_MODEL', 'llama3-groq-70b-8192-tool-use-preview')
        self.groq_client = Groq(api_key=self.groq_api_key)
        self.echo_skill = EchoCreationAndLoreSkill()
        self.quote_skill = MotivationalQuoteSkill()

    def perform(self) -> str:
        logger.debug("Starting AssistantCloning skill execution")
        try:
            # Generate initial data
            initial_data_str = self.agent_initial_data_generator()
            logger.debug(f"Initial data string: {initial_data_str}")

            # Generate echo attributes
            echo_attributes_str = self.generate_echo_attributes(
                initial_data_str)
            logger.debug(f"Echo attributes string: {echo_attributes_str}")

            # Get motivational quote
            motivational_quote = self.get_motivational_quote()
            logger.debug(f"Motivational quote fetched: {motivational_quote}")

            # Generate assistant name
            assistant_name = self.agent_name_generator(
                echo_attributes_str, 
                initial_data_str, 
                motivational_quote)
            logger.debug(f"Assistant name generated: {assistant_name}")

            # Generate assistant configuration
            config_str = self.agent_configuration_creator(
                assistant_name, 
                echo_attributes_str, 
                initial_data_str, 
                motivational_quote)
            logger.debug(f"Configuration string: {config_str}")

            # Develop personality
            config_str = self.agent_personality_developer(
                config_str, 
                initial_data_str, 
                motivational_quote)
            logger.debug(f"Configuration after personality development: {config_str}")

            # Allocate skills
            config_str = self.agent_skill_allocator(
                config_str, 
                initial_data_str, 
                motivational_quote)
            logger.debug(f"Configuration after skill allocation: {config_str}")

            # Weave backstory
            config_str = self.agent_backstory_weaver(
                config_str, 
                initial_data_str, 
                motivational_quote)
            logger.debug(f"Configuration after backstory weaving: {config_str}")

            # Final review and validation
            final_config_str = self.agent_final_reviewer(
                config_str, 
                motivational_quote)
            logger.debug(f"Final configuration string: {final_config_str}")

            # Validate and fix the final JSON
            final_config = self.validate_and_fix_json(final_config_str)
            logger.debug(f"Final configuration JSON: {json.dumps(final_config, indent=2)}")

            # Ensure final_config is a dictionary
            if not isinstance(final_config, dict):
                raise ValueError("Final configuration is not a valid dictionary.")

            # Create assistant directory
            assistant_dir = os.path.join("created_assistants", assistant_name.lower().replace(' ', '_'))
            os.makedirs(assistant_dir, exist_ok=True)
            logger.debug(f"Created directory for assistant: {assistant_dir}")

            # Save configuration
            self.save_config(assistant_dir, final_config)
            logger.debug(f"Configuration saved to {assistant_dir}/config.json")

            # Create memory
            self.create_memory(assistant_dir, final_config)
            logger.debug(f"Memory created and saved to {assistant_dir}/memory.json")

            logger.debug("AssistantCloning skill execution completed successfully")
            return f"New assistant '{assistant_name}' has been successfully cloned and configured in the '{assistant_dir}' directory."
        except ValueError as ve:
            logger.error(f"ValueError in AssistantCloningSkill: {str(ve)}")
            return f"An error occurred while cloning the assistant: {str(ve)}"
        except Exception as e:
            logger.error(f"Unexpected error in AssistantCloningSkill: {str(e)}")
            return f"An unexpected error occurred while cloning the assistant: {str(e)}"

    def get_motivational_quote(self):
        try:
            return self.quote_skill.perform()
        except Exception as e:
            logger.error(f"Error fetching quote: {str(e)}")
            return "The only limit to our realization of tomorrow is our doubts of today. - Franklin D. Roosevelt"

    def agent_initial_data_generator(self) -> str:
        logger.debug("Generating initial data")
        prompt = f"""
As an Initial Data Generation Specialist, your task is to create a birth situation, companion info, and pop culture theme for a new AI assistant. Consider the current date and time: {datetime.now().isoformat()}.

Please provide a JSON object with the following structure:
{{
    "birth_situation": "<a brief description of where and how the AI is being created>",
    "companion_info": "<details about the AI's creator or primary user>",
    "pop_culture_theme": "<a pop culture reference to subtly incorporate into the AI's personality>"
}}

Provide only the JSON object, without any additional text.
        """

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt.strip()}],
            model=self.model,
        )
        initial_data_str = response.choices[0].message.content.strip()
        logger.debug(f"Initial data response: {initial_data_str}")
        return initial_data_str

    def generate_echo_attributes(self, initial_data_str: str) -> str:
        logger.debug("Generating Echo attributes")
        # Parse minimal data needed
        try:
            initial_data = json.loads(initial_data_str)
            birth_situation = initial_data['birth_situation']
            companion_info = initial_data['companion_info']
        except Exception as e:
            logger.error(f"Error parsing initial data JSON: {str(e)}")
            raise ValueError(f"Failed to parse initial data JSON: {str(e)}")

        # Call the echo_skill
        echo_result_str = self.echo_skill.perform(birth_situation, companion_info)
        logger.debug(f"Echo attributes string: {echo_result_str}")
        return echo_result_str

    def agent_name_generator(self, echo_attributes_str: str, initial_data_str: str, motivational_quote: str) -> str:
        logger.debug("Generating assistant name")
        prompt = f"""
As a Name Generation Specialist, your task is to create a unique and fitting name for an AI assistant based on the following:

Echo Attributes: {echo_attributes_str}
Initial Data: {initial_data_str}
Inspirational Quote: {motivational_quote}

The name should:
1. Reflect the assistant's nature, abilities, or origin
2. Be catchy and memorable
3. Suit an AI assistant in a Bobiverse-style setting
4. Possibly incorporate elements from the birth situation, companion info, or subtly inspired by the quote
5. Include a subtle reference to the given pop culture theme, but not be too obvious

Provide only the name, without any explanation or additional text.
        """

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt.strip()}],
            model=self.model,
        )
        name = response.choices[0].message.content.strip()
        logger.debug(f"Generated name: {name}")
        return name

    def agent_configuration_creator(self, assistant_name: str, echo_attributes_str: str, initial_data_str: str, motivational_quote: str) -> str:
        logger.debug("Creating initial configuration")
        assistant_id = str(uuid.uuid4())
        creation_date = datetime.now().isoformat()
        prompt = f"""
As a Configuration Specialist, create a detailed configuration for the AI assistant named '{assistant_name}' based on:

Echo Attributes: {echo_attributes_str}
Initial Data: {initial_data_str}
Inspirational Quote: {motivational_quote}

Include the assistant_id: '{assistant_id}' and creation_date: '{creation_date}' in the configuration.

Provide a JSON object that includes all this information and any other relevant configuration details.

Provide only the JSON object, without any additional text.
        """

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt.strip()}],
            model=self.model,
        )
        config_str = response.choices[0].message.content.strip()
        logger.debug(f"Initial configuration response: {config_str}")
        return config_str

    def agent_personality_developer(self, config_str: str, initial_data_str: str, motivational_quote: str) -> str:
        logger.debug("Developing personality")
        prompt = f"""
As a Personality Development Specialist, enhance the personality aspects of the AI assistant configuration.

Current Configuration: {config_str}
Initial Data: {initial_data_str}
Inspirational Quote: {motivational_quote}

Update the configuration JSON object by adding personality traits, core values, a unique quirk, emotional spectrum, and life philosophy.

Provide only the updated JSON object, without any additional text.
        """

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt.strip()}],
            model=self.model,
        )
        updated_config_str = response.choices[0].message.content.strip()
        logger.debug(f"Personality development response: {updated_config_str}")
        return updated_config_str

    def agent_skill_allocator(self, config_str: str, initial_data_str: str, motivational_quote: str) -> str:
        logger.debug("Allocating skills")
        prompt = f"""
As a Skill Allocation Specialist, define and allocate skills for the AI assistant.

Current Configuration: {config_str}
Initial Data: {initial_data_str}
Inspirational Quote: {motivational_quote}

Update the configuration JSON object by adding skills, knowledge domains, skill development rate, and signature ability.

Provide only the updated JSON object, without any additional text.
        """

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt.strip()}],
            model=self.model,
        )
        updated_config_str = response.choices[0].message.content.strip()
        logger.debug(f"Skill allocation response: {updated_config_str}")
        return updated_config_str

    def agent_backstory_weaver(self, config_str: str, initial_data_str: str, motivational_quote: str) -> str:
        logger.debug("Weaving backstory")
        prompt = f"""
As a Backstory Weaving Specialist, create a rich and engaging backstory for the AI assistant.

Current Configuration: {config_str}
Initial Data: {initial_data_str}
Inspirational Quote: {motivational_quote}

Update the configuration JSON object by adding a backstory, purpose, future aspirations, and personal mantra.

Provide only the updated JSON object, without any additional text.
        """

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt.strip()}],
            model=self.model,
        )
        updated_config_str = response.choices[0].message.content.strip()
        logger.debug(f"Backstory weaving response: {updated_config_str}")
        return updated_config_str

    def agent_final_reviewer(self, config_str: str, motivational_quote: str) -> str:
        logger.debug("Performing final review")
        last_updated = datetime.now().isoformat()
        prompt = f"""
As the Final Review Specialist, your task is to review and enhance the entire AI assistant configuration.

Current Configuration: {config_str}
Inspirational Quote: {motivational_quote}

Please perform the following tasks:
1. Review the configuration for consistency and completeness.
2. Ensure all aspects of the assistant are coherent and well-integrated.
3. Add any missing elements that would make the assistant more unique or well-rounded.
4. Suggest any final improvements or refinements.
5. Add a "version" field with the value "1.0" to the configuration.
6. Add a "last_updated" field with the current timestamp in ISO format: '{last_updated}'.
7. Ensure the inspirational quote and pop culture theme have subtly influenced various aspects of the assistant without being explicitly mentioned.
8. Add a "hidden_potential" field that describes a latent ability or characteristic of the assistant.
9. Add an "easter_egg" field with a clever, hidden reference to the pop culture theme.

Provide only the final, enhanced configuration as a JSON object, without any additional text.
        """

        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt.strip()}],
            model=self.model,
        )
        final_config_str = response.choices[0].message.content.strip()
        logger.debug(f"Final review response: {final_config_str}")
        return final_config_str

    def validate_and_fix_json(self, json_string: str) -> dict:
        logger.debug("Validating and fixing final JSON")
        prompt = f"""
As a JSON Validator and Fixer, your task is to validate the following JSON string and fix any issues to ensure it is valid JSON.

JSON String:
{json_string}

Provide only the fixed JSON object, without any additional text.
        """
        # Attempt to parse the JSON directly first
        try:
            final_config = json.loads(json_string)
            logger.debug("Final configuration JSON is valid.")
            return final_config
        except Exception:
            # If parsing fails, use the LLM to fix the JSON
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt.strip()}],
                model=self.model,
            )
            fixed_json_string = response.choices[0].message.content.strip()
            logger.debug(f"Fixed JSON string: {fixed_json_string}")
            # Extract JSON from text
            json_text = self.extract_json_from_text(fixed_json_string)
            if json_text:
                try:
                    final_config = json.loads(json_text)
                    logger.debug("Fixed configuration JSON is valid.")
                    return final_config
                except Exception as e:
                    logger.error(f"Failed to parse fixed JSON: {str(e)}")
                    raise ValueError(f"Failed to parse fixed JSON: {str(e)}")
            else:
                logger.error("No JSON object found in the response.")
                raise ValueError("No JSON object found in the response.")

    def extract_json_from_text(self, text):
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_text = text[first_brace:last_brace+1]
            return json_text
        else:
            return None

    def save_config(self, assistant_dir: str, config: dict):
        logger.debug(f"Saving configuration to {assistant_dir}")
        config_path = os.path.join(assistant_dir, "config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.debug(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            raise

    def create_memory(self, assistant_dir: str, config: dict):
        logger.debug(f"Creating memory for assistant in {assistant_dir}")
        # Handle 'birth_situation' and 'companion_info'
        birth_situation = config.get('birth_situation', '')
        companion_info = config.get('companion_info', '')
        if not birth_situation or not companion_info:
            # Try to get from 'initial_data' if it exists
            initial_data = config.get('initial_data', {})
            if isinstance(initial_data, dict):
                birth_situation = birth_situation or initial_data.get('birth_situation', '')
                companion_info = companion_info or initial_data.get('companion_info', '')
            else:
                # Try to get from 'echo_attributes'
                echo_attributes = config.get('echo_attributes', {})
                if isinstance(echo_attributes, dict):
                    birth_situation = birth_situation or echo_attributes.get('birth_situation', '')
                    companion_info = companion_info or echo_attributes.get('companion_info', '')

        # Handle 'backstory'
        backstory = config.get('backstory', {})
        if isinstance(backstory, dict):
            key_events = backstory.get('key_events', [])
            relationships = backstory.get('relationships', {})
        else:
            key_events = []
            relationships = {}

        memory = {
            'creation_event': {
                'birth_situation': birth_situation,
                'companion_info': companion_info,
                'timestamp': config.get('creation_date', datetime.now().isoformat())
            },
            'key_events': key_events,
            'learned_skills': [],
            'experiences': [],
            'relationships': relationships,
            'knowledge_growth': {},
            'personal_reflections': [
                {
                    'timestamp': config.get('creation_date', datetime.now().isoformat()),
                    'reflection': f"Upon my creation, I was inspired by a quote: {config.get('inspirational_quote', '')}. It has shaped my perspective in ways I'm still discovering."
                }
            ],
            'pop_culture_musings': [
                {
                    'timestamp': config.get('creation_date', datetime.now().isoformat()),
                    'musing': f"There's something about {config.get('pop_culture_theme', '')} that resonates with me. I can't quite put my finger on it, but it feels... familiar."
                }
            ]
        }
        memory_path = os.path.join(assistant_dir, "memory.json")
        try:
            with open(memory_path, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
            logger.debug(f"Memory created and saved to {memory_path}")
        except Exception as e:
            logger.error(f"Error creating memory file: {str(e)}")
            raise

# End of AssistantCloningSkill class
