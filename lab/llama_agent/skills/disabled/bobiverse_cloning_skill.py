import os
import json
from skills.basic_skill import BasicSkill
from skills.echo_creation_skill import EchoCreationAndLoreSkill
import logging
from dotenv import load_dotenv
import uuid
from datetime import datetime
from groq import Groq
import traceback

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()


class ExceptionHandlingAgent:
    def __init__(self, groq_client, model):
        self.groq_client = groq_client
        self.model = model

    def handle_exception(self, error, context, step_name):
        error_message = str(error)
        stack_trace = traceback.format_exc()

        prompt = f"""
        As an AI exception handling agent, your task is to analyze the following error and suggest a fix or alternative approach:

        Error: {error_message}
        Stack Trace: {stack_trace}
        Context: {json.dumps(context, indent=2)}
        Failed Step: {step_name}

        Please provide:
        1. An analysis of what might have gone wrong
        2. A suggested fix or alternative approach
        3. Any additional data or input that might be needed
        4. A fallback solution if the issue cannot be fully resolved

        Respond in JSON format with the following structure:
        {{
            "analysis": "",
            "suggested_fix": "",
            "additional_data_needed": [],
            "fallback_solution": ""
        }}
        """

        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error in exception handling agent: {str(e)}")
            return {
                "analysis": "Unable to analyze error due to internal issue.",
                "suggested_fix": "Retry the operation or proceed with default values.",
                "additional_data_needed": [],
                "fallback_solution": "Use default configuration or skip the problematic step."
            }


class ExceptionRecoveryAgent:
    def __init__(self, groq_client, model):
        self.groq_client = groq_client
        self.model = model

    def process_exception_report(self, exception_report, original_context, step_name):
        prompt = f"""
        As an AI exception recovery agent, your task is to analyze the exception handling report and determine the exact data needed to retry the operation. 

        Exception Handling Report:
        {json.dumps(exception_report, indent=2)}

        Original Context:
        {json.dumps(original_context, indent=2)}

        Failed Step: {step_name}

        Please provide:
        1. A list of exact data fields needed for the retry attempt
        2. Any modifications needed to the original input data
        3. A step-by-step plan for the retry attempt

        Respond in JSON format with the following structure:
        {{
            "required_data_fields": [],
            "data_modifications": {{}},
            "retry_plan": []
        }}
        """

        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error in exception recovery agent: {str(e)}")
            return {
                "required_data_fields": [],
                "data_modifications": {},
                "retry_plan": ["Proceed with original data and method"]
            }


class SimplifiedEchoAssistantCreationSkill(BasicSkill):
    def __init__(self):
        self.name = 'SimplifiedEchoAssistantCreation'
        self.metadata = {
            'name': self.name,
            'description': 'Creates a new AI assistant based on Echo attributes, with robust exception handling and recovery.',
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
            raise ValueError(
                "GROQ_API_KEY not found in environment variables. Please set it in your .env file.")
        self.model = os.getenv(
            'LLM_MODEL', 'llama3-groq-70b-8192-tool-use-preview')
        self.groq_client = Groq(api_key=self.groq_api_key)
        self.echo_skill = EchoCreationAndLoreSkill()
        self.exception_agent = ExceptionHandlingAgent(
            self.groq_client, self.model)
        self.recovery_agent = ExceptionRecoveryAgent(
            self.groq_client, self.model)

    def perform(self, birth_situation: str, companion_info: str) -> str:
        context = {
            "birth_situation": birth_situation,
            "companion_info": companion_info
        }
        try:
            echo_result = self.execute_step(
                self.create_echo, context, "create_echo")
            assistant_name = self.execute_step(self.generate_assistant_name, {
                                               "echo_result": echo_result}, "generate_assistant_name")
            config = self.execute_step(self.create_assistant_config, {
                                       "assistant_name": assistant_name, "echo_result": echo_result, "birth_situation": birth_situation, "companion_info": companion_info}, "create_assistant_config")
            config = self.execute_step(self.agent_based_customization, {
                                       "config": config, "echo_result": echo_result}, "agent_based_customization")

            assistant_dir = os.path.join(
                "created_assistants", assistant_name.lower().replace(' ', '_'))
            os.makedirs(assistant_dir, exist_ok=True)

            self.execute_step(self.save_config, {
                              "assistant_dir": assistant_dir, "config": config}, "save_config")
            self.execute_step(self.create_memory, {
                              "assistant_dir": assistant_dir, "echo_result": echo_result, "config": config}, "create_memory")

            return f"New assistant '{assistant_name}' has been successfully created and configured in the '{assistant_dir}' directory."
        except Exception as e:
            logger.error(
                f"An unhandled error occurred in SimplifiedEchoAssistantCreationSkill: {str(e)}")
            return f"An unhandled error occurred while creating the assistant: {str(e)}"

    def execute_step(self, step_function, step_context, step_name):
        try:
            return step_function(**step_context)
        except Exception as e:
            logger.error(f"Error in {step_name}: {str(e)}")
            handler_result = self.exception_agent.handle_exception(
                e, step_context, step_name)
            logger.info(
                f"Exception handler suggestion for {step_name}: {handler_result}")

            recovery_result = self.recovery_agent.process_exception_report(
                handler_result, step_context, step_name)
            logger.info(
                f"Recovery agent result for {step_name}: {recovery_result}")

            if recovery_result['required_data_fields'] or recovery_result['data_modifications']:
                logger.info(
                    f"Attempting to retry {step_name} with recovery agent suggestions")
                try:
                    for key, value in recovery_result['data_modifications'].items():
                        if key in step_context:
                            step_context[key] = value
                        else:
                            step_context[key] = self.generate_missing_data(
                                key, value, step_context)

                    for field in recovery_result['required_data_fields']:
                        if field not in step_context:
                            step_context[field] = self.generate_missing_data(
                                field, None, step_context)

                    for step in recovery_result['retry_plan']:
                        logger.info(f"Executing retry step: {step}")

                    return step_function(**step_context)
                except Exception as retry_error:
                    logger.error(
                        f"Error in retry of {step_name}: {str(retry_error)}")

            return self.apply_fallback_solution(handler_result['fallback_solution'], step_name, step_context)

    def generate_missing_data(self, data_item, suggested_value, context):
        prompt = f"""
        Generate a suitable value for the missing data item: {data_item}
        Suggested value (if any): {suggested_value}
        Context: {json.dumps(context, indent=2)}

        Provide a single value that would be appropriate for this data item given the context.
        """

        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(
                f"Error generating missing data for {data_item}: {str(e)}")
            return f"Default_{data_item}"

    def apply_fallback_solution(self, fallback_solution, step_name, context):
        logger.info(
            f"Applying fallback solution for {step_name}: {fallback_solution}")
        if step_name == "create_echo":
            return {"attributes": {"name": "Default Echo", "type": "Generic", "elemental_affinity": "None"}}
        elif step_name == "generate_assistant_name":
            return "DefaultAssistant"
        elif step_name == "create_assistant_config":
            return self.create_default_config(context.get('assistant_name', 'DefaultAssistant'))
        elif step_name == "agent_based_customization":
            return context.get('config', self.create_default_config('DefaultAssistant'))
        elif step_name == "save_config" or step_name == "create_memory":
            logger.warning(f"Skipping {step_name} due to unresolvable error")
            return None
        else:
            return None

    def create_default_config(self, assistant_name):
        return {
            'assistant_name': assistant_name,
            'assistant_id': str(uuid.uuid4()),
            'echo_attributes': {},
            'birth_situation': 'Default creation',
            'companion_info': 'No companion information available',
            'creation_date': datetime.now().isoformat(),
            'characteristic_description': 'A basic AI assistant with default capabilities',
            'personality_traits': ['Helpful', 'Adaptive', 'Resourceful'],
            'base_skills': ['Communication', 'Problem Solving', 'Information Retrieval'],
            'lore': 'No specific lore available',
            'extended_lore': {},
            'background_summary': 'A default assistant created without specific Echo attributes'
        }

    def create_echo(self, birth_situation: str, companion_info: str):
        echo_result = json.loads(self.echo_skill.perform(
            birth_situation, companion_info))
        return echo_result

    def generate_assistant_name(self, echo_result: dict) -> str:
        echo_attributes = echo_result['attributes']
        prompt = f"""
        Generate a unique and fitting name for an AI assistant based on the following Echo attributes:
        {json.dumps(echo_attributes, indent=2)}

        The name should reflect the assistant's nature, abilities, or origin. It should be catchy and memorable.
        Provide only the name, without any additional explanation.
        """

        messages = [
            {"role": "system", "content": "You are an AI specialized in creating unique and fitting names for AI assistants."},
            {"role": "user", "content": prompt}
        ]

        response = self.groq_client.chat.completions.create(
            messages=messages,
            model=self.model,
        )
        return response.choices[0].message.content.strip()

    def create_assistant_config(self, assistant_name: str, echo_result: dict, birth_situation: str, companion_info: str) -> dict:
        echo_attributes = echo_result['attributes']
        return {
            'assistant_name': assistant_name,
            'assistant_id': str(uuid.uuid4()),
            'echo_attributes': echo_attributes,
            'birth_situation': birth_situation,
            'companion_info': companion_info,
            'creation_date': datetime.now().isoformat(),
            'characteristic_description': echo_attributes.get('description', 'A unique AI assistant with specialized capabilities'),
            'personality_traits': [],
            'base_skills': [],
            'lore': echo_attributes.get('lore', ''),
            'extended_lore': echo_result.get('extended_lore', {})
        }

    def agent_based_customization(self, config: dict, echo_result: dict) -> dict:
        prompt = f"""
        As an AI agent specializing in assistant customization and validation, your task is to review and enhance the configuration for a newly created AI assistant. 
        Consider the following:

        1. Echo Attributes: {json.dumps(echo_result['attributes'], indent=2)}
        2. Extended Lore: {json.dumps(echo_result['extended_lore'], indent=2)}
        3. Current Configuration: {json.dumps(config, indent=2)}

        Please perform the following tasks:

        1. Validate the configuration for consistency and completeness.
        2. Suggest improvements or additions to make the assistant unique and well-suited to its Echo attributes and lore.
        3. Refine the 'characteristic_description' to better reflect the assistant's unique traits and origin.
        4. Generate a list of personality traits (at least 5) that fit the assistant's Echo attributes and lore.
        5. Suggest a list of base skills (at least 5) that the assistant should have, considering its purpose and attributes.
        6. Create a brief summary of the assistant's background based on the Echo's lore and extended lore.

        Provide your response as a JSON object with the following structure:
        {{
            "validated_config": {{}},
            "personality_traits": [],
            "base_skills": [],
            "background_summary": "",
            "validation_notes": ""
        }}
        """

        messages = [
            {"role": "system", "content": "You are an AI specialized in customizing and validating assistant configurations."},
            {"role": "user", "content": prompt}
        ]

        response = self.groq_client.chat.completions.create(
            messages=messages,
            model=self.model,
        )
        result = json.loads(response.choices[0].message.content)

        config.update(result['validated_config'])
        config['personality_traits'] = result['personality_traits']
        config['base_skills'] = result['base_skills']
        config['background_summary'] = result['background_summary']
        config['validation_notes'] = result['validation_notes']

        return config

    def save_config(self, assistant_dir: str, config: dict):
        config_path = os.path.join(assistant_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def create_memory(self, assistant_dir: str, echo_result: dict, config: dict):
        memory = {
            'creation_event': {
                'birth_situation': config['birth_situation'],
                'companion_info': config['companion_info'],
                'timestamp': datetime.now().isoformat()
            },
            'echo_origin': echo_result['attributes']['origin'],
            'lore': config['lore'],
            'extended_lore': config['extended_lore'],
            'background_summary': config['background_summary'],
            'experiences': [],
            'learned_skills': config['base_skills'],
            'relationships': [{'type': 'companion', 'info': config['companion_info']}],
            'personality_growth': []
        }
        memory_path = os.path.join(assistant_dir, "memory.json")
        with open(memory_path, 'w') as f:
            json.dump(memory, f, indent=2)

# End of SimplifiedEchoAssistantCreationSkill class
