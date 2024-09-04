from skills.basic_skill import BasicSkill
import json
import os
from datetime import datetime
from openai import AzureOpenAI
import requests
import uuid

class Echo:
    def __init__(self, **attributes):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        self.__dict__.update(attributes)

class CreateSpecificEchoSkill(BasicSkill):
    def __init__(self):
        self.name = "CreateSpecificEcho"
        self.metadata = {
            "name": self.name,
            "description": "Creates a highly detailed and unique Echo with numerous customizable attributes. The skill uses Azure OpenAI to generate Echo details and optionally creates a visual representation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attributes": {
                        "type": "object",
                        "description": "A dictionary of attributes that define the Echo. Can include any number of custom fields.",
                        "properties": {
                            "name": {"type": "string", "description": "The Echo's name"},
                            "type": {"type": "string", "description": "The Echo's primary type or classification"},
                            "elemental_affinity": {"type": "string", "description": "The Echo's elemental alignment"},
                            "rarity": {"type": "string", "description": "How rare this Echo is"},
                            "size": {"type": "string", "description": "The Echo's size or size range"},
                            "weight": {"type": "string", "description": "The Echo's weight or weight range"},
                            "lifespan": {"type": "string", "description": "The Echo's expected lifespan"},
                            "habitat": {"type": "string", "description": "The Echo's preferred living environment"},
                            "diet": {"type": "string", "description": "What the Echo consumes for sustenance"},
                            "behavior": {"type": "string", "description": "The Echo's typical behavior patterns"},
                            "intelligence": {"type": "string", "description": "The Echo's level of intelligence"},
                            "communication": {"type": "string", "description": "How the Echo communicates"},
                            "special_abilities": {"type": "array", "items": {"type": "string"}, "description": "List of the Echo's unique abilities"},
                            "weaknesses": {"type": "array", "items": {"type": "string"}, "description": "List of the Echo's vulnerabilities"},
                            "physical_characteristics": {
                                "type": "object",
                                "properties": {
                                    "body_shape": {"type": "string"},
                                    "limbs": {"type": "string"},
                                    "skin_texture": {"type": "string"},
                                    "color_scheme": {"type": "string"},
                                    "distinguishing_features": {"type": "array", "items": {"type": "string"}}
                                }
                            },
                            "elemental_properties": {
                                "type": "object",
                                "properties": {
                                    "primary_element": {"type": "string"},
                                    "secondary_elements": {"type": "array", "items": {"type": "string"}},
                                    "elemental_resistances": {"type": "array", "items": {"type": "string"}},
                                    "elemental_weaknesses": {"type": "array", "items": {"type": "string"}}
                                }
                            },
                            "lifecycle": {
                                "type": "object",
                                "properties": {
                                    "birth": {"type": "string"},
                                    "growth_stages": {"type": "array", "items": {"type": "string"}},
                                    "maturity": {"type": "string"},
                                    "reproduction": {"type": "string"},
                                    "death": {"type": "string"}
                                }
                            },
                            "social_structure": {"type": "string", "description": "The Echo's social behaviors and hierarchies"},
                            "symbiotic_relationships": {"type": "array", "items": {"type": "string"}, "description": "Other species the Echo has beneficial relationships with"},
                            "environmental_impact": {"type": "string", "description": "How the Echo affects its surroundings"},
                            "magical_properties": {"type": "array", "items": {"type": "string"}, "description": "Any magical attributes or effects associated with the Echo"},
                            "cultural_significance": {"type": "string", "description": "The Echo's importance in local legends or cultures"},
                            "game_mechanics": {
                                "type": "object",
                                "properties": {
                                    "base_stats": {
                                        "type": "object",
                                        "properties": {
                                            "health": {"type": "integer"},
                                            "attack": {"type": "integer"},
                                            "defense": {"type": "integer"},
                                            "speed": {"type": "integer"},
                                            "special_attack": {"type": "integer"},
                                            "special_defense": {"type": "integer"}
                                        }
                                    },
                                    "ability_cooldowns": {"type": "object"},
                                    "evolution_triggers": {"type": "array", "items": {"type": "string"}},
                                    "loot_table": {"type": "array", "items": {"type": "string"}}
                                }
                            },
                            "lore": {"type": "string", "description": "Brief background story or myth about the Echo"},
                            "discovery_information": {
                                "type": "object",
                                "properties": {
                                    "discovered_by": {"type": "string"},
                                    "discovery_date": {"type": "string"},
                                    "discovery_location": {"type": "string"}
                                }
                            }
                        }
                    },
                    "generate_image": {
                        "type": "boolean",
                        "description": "Whether to generate an image for the Echo."
                    },
                    "image_prompt": {
                        "type": "string",
                        "description": "Custom prompt for image generation, if different from the Echo description."
                    }
                },
                "required": ['attributes']
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        # Load API configuration
        with open('config/api_keys.json', 'r') as api_keys_file:
            self.api_keys = json.load(api_keys_file)

        self.gpt_client = AzureOpenAI(
            api_version=self.api_keys['azure_openai_api_version'],
            azure_endpoint=self.api_keys['azure_openai_endpoint'],
            api_key=self.api_keys['azure_openai_api_key'],
        )

        self.dalle_client = AzureOpenAI(
            api_version=self.api_keys.get('dalle_api_version', self.api_keys['azure_openai_api_version']),
            azure_endpoint=self.api_keys.get('dalle_azure_endpoint', self.api_keys['azure_openai_endpoint']),
            api_key=self.api_keys.get('dalle_api_key', self.api_keys['azure_openai_api_key']),
        )

    def perform(self, **kwargs):
        attributes = kwargs['attributes']
        generate_image = kwargs.get('generate_image', False)
        image_prompt = kwargs.get('image_prompt', '')

        try:
            # Generate a description based on the attributes
            description_prompt = f"Create a detailed description of an Echo with the following attributes:\n"
            for key, value in attributes.items():
                description_prompt += f"{key}: {json.dumps(value)}\n"
            description_prompt += "\nProvide the description as a single paragraph."

            description_response = self.gpt_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a creative assistant designed to generate unique magical creatures called Echoes for a game."},
                    {"role": "user", "content": description_prompt}
                ],
                max_tokens=500,
                n=1,
                stop=None,
                temperature=0.7,
            )

            description = description_response.choices[0].message.content.strip()
            attributes['description'] = description

            image_path = None
            if generate_image:
                image_prompt = image_prompt or f"Create an image of a magical creature with these attributes: {description}"
                
                image_result = self.dalle_client.images.generate(
                    model='Dalle3',
                    prompt=image_prompt,
                    n=1
                )

                image_url = json.loads(image_result.model_dump_json())['data'][0]['url']

                # Download and save the image
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    os.makedirs(self.api_keys['image_dir'], exist_ok=True)
                    downloaded_image_filename = f"echo_{attributes.get('name', 'unnamed').replace(' ', '_').lower()}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
                    image_path = os.path.join(self.api_keys['image_dir'], downloaded_image_filename)
                    with open(image_path, 'wb') as file:
                        file.write(image_response.content)
                    attributes['image_path'] = image_path
                else:
                    print(f"Failed to download the generated image. Status code: {image_response.status_code}")

            echo = Echo(**attributes)
            
            # Create a consistent, machine-readable output
            output = {
                "echo_id": echo.id,
                "created_at": echo.created_at,
                "attributes": echo.__dict__
            }

            # Remove id and created_at from nested attributes to avoid duplication
            output["attributes"].pop("id", None)
            output["attributes"].pop("created_at", None)

            return json.dumps(output, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

# Example usage:
# skill = CreateSpecificEchoSkill()
# result = skill.perform(
#     attributes={
#         "name": "Zephyrix",
#         "type": "Elemental",
#         "elemental_affinity": "Air",
#         "rarity": "Legendary",
#         "size": "Varies from 1cm to 10m",
#         "weight": "Nearly weightless",
#         "lifespan": "Eternal",
#         "habitat": "High altitude regions, storm fronts",
#         "diet": "Electric charge and kinetic energy",
#         "behavior": "Unpredictable, driven by wind patterns",
#         "intelligence": "Hivemind-like collective consciousness",
#         "communication": "Whistles, gusts, and electrical discharges",
#         "special_abilities": ["Weather manipulation", "Electrical generation", "Invisibility in air currents"],
#         "weaknesses": ["Grounding effects", "Vacuum environments"],
#         "physical_characteristics": {
#             "body_shape": "Amorphous, cloud-like",
#             "limbs": "Tentacle-like wind currents",
#             "skin_texture": "Misty, with occasional spark discharges",
#             "color_scheme": "Shifting blues and whites with electric yellow accents",
#             "distinguishing_features": ["Lightning bolt patterns", "Swirling eye-like vortexes"]
#         },
#         "elemental_properties": {
#             "primary_element": "Air",
#             "secondary_elements": ["Lightning", "Sound"],
#             "elemental_resistances": ["Air", "Electric", "Cold"],
#             "elemental_weaknesses": ["Earth", "Fire"]
#         },
#         "lifecycle": {
#             "birth": "Spontaneous formation in powerful storms",
#             "growth_stages": ["Wisp", "Breeze", "Gale", "Tempest"],
#             "maturity": "Achieved when able to form its own storm system",
#             "reproduction": "Splitting during particularly intense weather phenomena",
#             "death": "Dissipation into the atmosphere, becoming one with the global air currents"
#         },
#         "social_structure": "Loosely connected collective, gathering in larger storm systems",
#         "symbiotic_relationships": ["Lightning birds", "Cloud whales", "Storm dragons"],
#         "environmental_impact": "Vital for global weather patterns and atmospheric energy distribution",
#         "magical_properties": ["Can store and release magical energies", "Enhances air and light