from skills.basic_skill import BasicSkill
import json
import os
from datetime import datetime
from openai import AzureOpenAI
import requests

class Echo:
    def __init__(self, name, type, description, level=1, image_path=None):
        self.name = name
        self.type = type
        self.description = description
        self.level = level
        self.happiness = 50
        self.energy = 100
        self.experience = 0
        self.image_path = image_path

class CreateSpecificEchoSkill(BasicSkill):
    def __init__(self):
        self.name = "CreateSpecificEcho"
        self.metadata = {
            "name": self.name,
            "description": "Creates a specific echo based on environmental factors for the game 'Echo Guardians.' The skill uses Azure OpenAI to generate unique Echoes with attributes such as name, type, and description, and creates a visual representation using DALL-E 3.",
            "parameters": {
                "type": "object",
                "properties": {
                    "environment": {"type": "string", "description": "The type of environment (e.g., forest, desert, ocean)"},
                    "time_of_day": {"type": "string", "description": "The time of day (e.g., dawn, noon, dusk, midnight)"},
                    "weather": {"type": "string", "description": "The current weather conditions"},
                    "mood": {"type": "string", "description": "The overall mood or atmosphere of the scene"},
                    "additional_context": {"type": "string", "description": "Any additional context or specific elements to consider"}
                },
                "required": ['environment', 'time_of_day', 'weather', 'mood']
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        # Load API configuration
        with open('config/api_keys.json', 'r') as api_keys_file:
            api_keys = json.load(api_keys_file)

        # Initialize the AzureOpenAI client for GPT
        self.gpt_client = AzureOpenAI(
            api_version=api_keys['azure_openai_api_version'],
            azure_endpoint=api_keys['azure_openai_endpoint'],
            api_key=api_keys['azure_openai_api_key'],
        )

        # Initialize the AzureOpenAI client for DALL-E
        self.dalle_client = AzureOpenAI(
            api_version=api_keys.get('dalle_api_version', api_keys['azure_openai_api_version']),
            azure_endpoint=api_keys.get('dalle_azure_endpoint', api_keys['azure_openai_endpoint']),
            api_key=api_keys.get('dalle_api_key', api_keys['azure_openai_api_key']),
        )
        
        self.image_dir = "echo_images"
        os.makedirs(self.image_dir, exist_ok=True)

    def perform(self, environment: str, time_of_day: str, weather: str, mood: str, additional_context: str = "") -> str:
        try:
            prompt = f"""
            Create a unique Echo for the game 'Echo Guardians' based on the following environmental factors:
            Environment: {environment}
            Time of Day: {time_of_day}
            Weather: {weather}
            Mood: {mood}
            Additional Context: {additional_context}

            Provide the Echo's details in JSON format with the following structure:
            {{
                "name": "Echo's name",
                "type": "Echo's elemental or thematic type",
                "description": "A vivid description of the Echo"
            }}
            """

            response = self.gpt_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a creative assistant designed to generate unique magical creatures called Echoes for a game."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                n=1,
                stop=None,
                temperature=0.8,
            )

            echo_data = json.loads(response.choices[0].message.content)
            
            # Generate image using DALL-E
            image_prompt = f"Create a magical creature called an Echo with these traits: {echo_data['description']}. It should be in a {environment} during {time_of_day} with {weather} weather. The mood is {mood}. {additional_context}"
            
            image_result = self.dalle_client.images.generate(
                model="Dalle3",
                prompt=image_prompt,
                n=1
            )

            image_url = json.loads(image_result.model_dump_json())['data'][0]['url']

            # Download and save the image
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                downloaded_image_filename = f"echo_{echo_data['name'].replace(' ', '_').lower()}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
                image_path = os.path.join(self.image_dir, downloaded_image_filename)
                with open(image_path, 'wb') as file:
                    file.write(image_response.content)
            else:
                image_path = None
                print(f"Failed to download the generated image. Status code: {image_response.status_code}")

            echo = Echo(echo_data['name'], echo_data['type'], echo_data['description'], image_path=image_path)
            
            result = f"""Created Echo: {echo.name} (Type: {echo.type}, Level: {echo.level})
Description: {echo.description}
"""
            if image_path:
                result += f"Image: {echo.image_path}\n"
            else:
                result += "Image generation failed. No image available.\n"

            result += f"""
Environmental Factors:
Environment: {environment}
Time of Day: {time_of_day}
Weather: {weather}
Mood: {mood}
Additional Context: {additional_context}"""

            return result

        except Exception as e:
            return f"An error occurred while creating the Echo: {str(e)}"

# Example usage:
# skill = CreateSpecificEchoSkill()
# result = skill.perform(
#     environment="Misty mountain forest",
#     time_of_day="Dawn",
#     weather="Light drizzle with fog",
#     mood="Mysterious and serene",
#     additional_context="Ancient ruins nearby"
# )
# print(result)