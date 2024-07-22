from skills.basic_skill import BasicSkill
from PIL import Image, ImageDraw
import random
import os
from datetime import datetime
import os
from openai import AzureOpenAI
import json
import requests
import time

class ArtGeneratorSkill(BasicSkill):
    def __init__(self):
        self.name = 'ArtGenerator'
        self.metadata = {
            'name': self.name,
            'description': 'Generates art using the DALL-E 3 API based on textual instructions and saves it to an "art" subfolder.',
            'parameters': {
                'type': 'object',
                'properties': {
                    "description": {
                        "type": "string",
                        "description": "The text prompt to generate the artwork from."
                    }
                },
                'required': ["description"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        # Load API configuration
        with open('config/api_keys.json', 'r') as api_keys_file:
            api_keys = json.load(api_keys_file)

        # Initialize the AzureOpenAI client for DALLE
        self.client = AzureOpenAI(
            api_version=api_keys.get('dalle_api_version', api_keys['azure_openai_api_version']),
            azure_endpoint=api_keys.get('dalle_azure_endpoint', api_keys['azure_openai_endpoint']),
            api_key=api_keys.get('dalle_api_key', api_keys['azure_openai_api_key']),
        )

    def perform(self, description):
        # Call the Azure OpenAI API
        result = self.client.images.generate(
            model="Dalle3",
            prompt=description,
            n=1
        )

        image_url = json.loads(result.model_dump_json())['data'][0]['url']

        # Download and save the image from the URL
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            # Create an 'art' directory if it doesn't exist
            if not os.path.exists('art'):
                os.makedirs('art')
            downloaded_image_filename = 'generated_art_' + \
                datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.png'
            with open(os.path.join('art', downloaded_image_filename), 'wb') as file:
                file.write(image_response.content)
            return 'Downloaded and saved in the art folder.' + ' Image filename: ' + '~/art/' + downloaded_image_filename + '.png' + ' Image URL: ' + image_url
        else:
            return "Failed to download the generated image."