from skills.basic_skill import BasicSkill
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import json
import os
import requests
from datetime import datetime
import uuid
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Echo:
    def __init__(self, **attributes):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        self.__dict__.update(attributes)

class EchoCreationAndLoreSkill(BasicSkill):
    def __init__(self):
        self.name = "EchoCreationAndLore"
        self.metadata = {
            "name": self.name,
            "description": "Creates a detailed Echo with customizable attributes and produces comprehensive lore including the Echo's experiences and potential evolution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "birth_situation": {"type": "string", "description": "The situation where the Echo is born"},
                    "companion_info": {"type": "string", "description": "Information about the Echo's companion"}
                },
                "required": ["birth_situation", "companion_info"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        # Initialize Groq client
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")
        self.model = os.getenv('LLM_MODEL', 'llama3-groq-70b-8192-tool-use-preview')
        self.chatbot = ChatGroq(model=self.model, groq_api_key=self.groq_api_key)

        self.lore_dir = os.path.join(os.getcwd(), 'echoverse_lore')
        os.makedirs(self.lore_dir, exist_ok=True)

        # Define rarity tiers and their probabilities
        self.rarity_tiers = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"]
        self.rarity_probabilities = [0.50, 0.25, 0.15, 0.07, 0.02, 0.01]

        # Define natures and their effects
        self.natures = ["Hardy", "Lonely", "Brave", "Adamant", "Naughty", "Bold", "Docile", "Relaxed", "Impish", "Lax", "Timid", "Hasty", "Serious", "Jolly", "Naive", "Modest", "Mild", "Quiet", "Bashful", "Rash", "Calm", "Gentle", "Sassy", "Careful", "Quirky"]
        self.nature_effects = {
            "Lonely": {"attack": 1.1, "defense": 0.9},
            "Brave": {"attack": 1.1, "speed": 0.9},
            "Adamant": {"attack": 1.1, "special_attack": 0.9},
            "Naughty": {"attack": 1.1, "special_defense": 0.9},
            "Bold": {"defense": 1.1, "attack": 0.9},
            "Relaxed": {"defense": 1.1, "speed": 0.9},
            "Impish": {"defense": 1.1, "special_attack": 0.9},
            "Lax": {"defense": 1.1, "special_defense": 0.9},
            "Timid": {"speed": 1.1, "attack": 0.9},
            "Hasty": {"speed": 1.1, "defense": 0.9},
            "Jolly": {"speed": 1.1, "special_attack": 0.9},
            "Naive": {"speed": 1.1, "special_defense": 0.9},
            "Modest": {"special_attack": 1.1, "attack": 0.9},
            "Mild": {"special_attack": 1.1, "defense": 0.9},
            "Quiet": {"special_attack": 1.1, "speed": 0.9},
            "Rash": {"special_attack": 1.1, "special_defense": 0.9},
            "Calm": {"special_defense": 1.1, "attack": 0.9},
            "Gentle": {"special_defense": 1.1, "defense": 0.9},
            "Sassy": {"special_defense": 1.1, "speed": 0.9},
            "Careful": {"special_defense": 1.1, "special_attack": 0.9}
        }

        # Define moods
        self.moods = ["Joyful", "Curious", "Excited", "Calm", "Anxious", "Mischievous", "Tired", "Energetic", "Grumpy", "Affectionate"]

        # Define unique quirks
        self.quirks = [
            "Glows in the dark", "Levitates while sleeping", "Changes color with mood",
            "Sings melodies that affect weather", "Leaves a trail of sparkles",
            "Can temporarily merge with its element", "Telepathic with plants",
            "Creates miniature copies of itself", "Phases through solid objects",
            "Absorbs and reflects light in dazzling patterns"
        ]

    def perform(self, birth_situation: str, companion_info: str) -> str:
        print("[DEBUG] Starting Echo creation process...")
        try:
            # Generate core Echo attributes based on birth situation and companion
            echo_attributes = self.generate_core_attributes(birth_situation, companion_info)
            if not echo_attributes:
                raise ValueError("Failed to generate core attributes")

            # Generate additional attributes
            echo_attributes.update({
                "rarity": self.generate_rarity(),
                "base_stats": self.generate_base_stats(),
                "echo_values": self.generate_echo_values(),
                "echo_potential": self.generate_echo_potential(),
                "nature": self.generate_nature(),
                "resonance_level": self.generate_resonance_level(),
                "elemental_affinity_strength": self.generate_elemental_affinity_strength(),
                "adaptability": self.generate_adaptability(),
                "lifespan": self.generate_lifespan(),
                "mood": self.generate_mood(),
                "unique_quirk": self.generate_unique_quirk()
            })

            # Apply nature effects to base stats
            self.apply_nature_effects(echo_attributes)

            # Fetch a motivational quote
            echo_attributes['motivational_quote'] = self.fetch_quote()

            # Generate Echo description and lore
            description, lore = self.generate_echo_details(echo_attributes, birth_situation, companion_info)
            echo_attributes['description'] = description
            echo_attributes['lore'] = lore

            # Create the Echo instance
            echo = Echo(**echo_attributes)

            # Generate extended lore
            extended_lore = self.generate_extended_lore(echo, echo_attributes.get('num_lore_sections', 5), 
                                                        echo_attributes.get('lore_focus', ["origin", "abilities", "habitat"]), 
                                                        birth_situation)

            # Combine all results
            final_result = {
                "echo_id": echo.id,
                "created_at": echo.created_at,
                "attributes": echo.__dict__,
                "extended_lore": extended_lore
            }

            # Save the result to a JSON file
            self.save_echo_to_json(final_result)

            print("[DEBUG] Echo creation process completed successfully.")
            return json.dumps(final_result, indent=2)

        except ValueError as ve:
            print(f"[DEBUG] Value error occurred: {str(ve)}")
            return json.dumps({"error": str(ve)}, indent=2)
        except Exception as e:
            print(f"[DEBUG] Unexpected error occurred: {str(e)}")
            return json.dumps({"error": f"An unexpected error occurred: {str(e)}"}, indent=2)

    def generate_core_attributes(self, birth_situation, companion_info):
        print("[DEBUG] Generating core Echo attributes...")
        prompt = f"""
        Generate core attributes for a unique Echo based on the following:
        Birth Situation: {birth_situation}
        Companion Information: {companion_info}

        Provide the following attributes, one per line, in the format 'attribute: value':
        1. name
        2. type
        3. elemental_affinity
        4. size
        5. habitat
        6. abilities (list of 3-5, comma-separated)
        7. personality
        8. origin
        9. evolution_stage
        10. weaknesses (list of 2-3, comma-separated)
        11. strengths (list of 2-3, comma-separated)

        Ensure that the attributes are cohesive and reflect both the birth situation and the companion's characteristics.
        """

        messages = [
            SystemMessage(content="You are an AI designed to generate unique and interesting Echoes based on given contexts."),
            HumanMessage(content=prompt)
        ]

        response = self.chatbot.invoke(messages)
        content = response.content.strip()

        # Parse the response and convert it into a dictionary
        attributes = {}
        for line in content.split('\n'):
            parts = line.split(':', 1)
            if len(parts) == 2:
                key, value = parts
                # Remove the number and any leading/trailing whitespace from the key
                key = key.split('.', 1)[-1].strip().lower().replace(' ', '_')
                value = value.strip()
                if key in ['abilities', 'weaknesses', 'strengths']:
                    value = [item.strip() for item in value.split(',')]
                attributes[key] = value

        # Ensure all required attributes are present
        required_attributes = ['name', 'type', 'elemental_affinity', 'size', 'habitat', 'abilities', 
                               'personality', 'origin', 'evolution_stage', 'weaknesses', 'strengths']
        for attr in required_attributes:
            if attr not in attributes:
                print(f"[DEBUG] Missing required attribute: {attr}")
                attributes[attr] = f"Default {attr.capitalize()}"

        print(f"[DEBUG] Generated attributes: {attributes}")
        return attributes

    def generate_rarity(self):
        return np.random.choice(self.rarity_tiers, p=self.rarity_probabilities)

    def generate_base_stats(self):
        return {stat: np.random.randint(40, 256) for stat in ["hp", "attack", "defense", "special_attack", "special_defense", "speed"]}

    def generate_echo_values(self):
        return {stat: np.random.randint(0, 253) for stat in ["hp", "attack", "defense", "special_attack", "special_defense", "speed"]}

    def generate_echo_potential(self):
        return {stat: np.random.randint(0, 32) for stat in ["hp", "attack", "defense", "special_attack", "special_defense", "speed"]}

    def generate_nature(self):
        return np.random.choice(self.natures)

    def generate_resonance_level(self):
        return np.random.randint(1, 101)

    def generate_elemental_affinity_strength(self):
        return np.random.randint(1, 101)

    def generate_adaptability(self):
        return np.random.randint(1, 101)

    def generate_lifespan(self):
        return np.random.randint(50, 1001)  # Lifespan in years

    def generate_mood(self):
        return np.random.choice(self.moods)

    def generate_unique_quirk(self):
        return np.random.choice(self.quirks)

    def apply_nature_effects(self, echo_attributes):
        nature = echo_attributes["nature"]
        if nature in self.nature_effects:
            for stat, modifier in self.nature_effects[nature].items():
                echo_attributes["base_stats"][stat] = int(echo_attributes["base_stats"][stat] * modifier)

    def fetch_quote(self):
        try:
            response = requests.get("https://api.forismatic.com/api/1.0/?method=getQuote&lang=en&format=jsonp&jsonp=?")
            # Remove the leading '(' and trailing ')' before parsing JSON
            cleaned_data = response.text.strip('()').strip()
            data = json.loads(cleaned_data)
            quote = data['quoteText']
            author = data['quoteAuthor']
            return f"Quote: {quote}\nAuthor: {author}"
        except Exception as e:
            print(f"[DEBUG] Error fetching quote: {str(e)}")
            return "Unable to fetch quote at this time."

    def generate_echo_details(self, attributes, birth_situation, companion_info):
        description_prompt = f"""
        Create a detailed description of an Echo with the following attributes:
        {json.dumps(attributes, indent=2)}

        Birth Situation: {birth_situation}
        Companion Information: {companion_info}

        Provide the description as a single paragraph. Ensure the Echo fits within the given birth situation while emphasizing its unique features and connection to its companion.
        """

        lore_prompt = f"""
        Create a brief lore and cultural significance for the Echo named {attributes.get('name', 'the Echo')} based on its attributes, birth situation, and companion.
        Include any myths, legends, or cultural importance associated with this Echo in the game world.
        Use the following quote as inspiration for a vague parable or legend within the lore, but do not directly include the quote itself: "{attributes.get('motivational_quote', 'No quote available')}"

        Birth Situation: {birth_situation}
        Companion Information: {companion_info}
        """

        description_messages = [
            SystemMessage(content="You are a creative assistant designed to generate unique magical creatures called Echoes for a game."),
            HumanMessage(content=description_prompt)
        ]

        lore_messages = [
            SystemMessage(content="You are a creative writer crafting lore and cultural significance for magical creatures in a game world."),
            HumanMessage(content=lore_prompt)
        ]

        description_response = self.chatbot.invoke(description_messages)
        lore_response = self.chatbot.invoke(lore_messages)

        return description_response.content.strip(), lore_response.content.strip()

    def generate_extended_lore(self, echo, num_sections, lore_focus, birth_situation):
        lore_aspect = f"The Life and Evolution of {echo.name}"

        # Generate lore concept
        concept = self.generate_lore_concept(lore_aspect, echo, lore_focus, birth_situation)

        # Generate lore outline
        outline = self.generate_lore_outline(lore_aspect, concept, lore_focus)

        # Generate section summaries
        summaries = self.generate_section_summaries(lore_aspect, outline, lore_focus)

        # Generate full lore
        full_lore = self.generate_full_lore(lore_aspect, summaries, num_sections, birth_situation)

        return full_lore

    def generate_lore_concept(self, lore_aspect, echo, lore_focus, birth_situation):
        prompt = f"""
        Generate a high-level concept for the lore of {echo.name}, focusing on {lore_aspect}.
        Consider the following aspects:
        - Echo attributes: {json.dumps(echo.__dict__, indent=2)}
        - Lore focus: {', '.join(lore_focus)}
        - Birth situation: {birth_situation}

        Provide a brief paragraph describing the overall concept and theme of the lore.
        """

        messages = [
            SystemMessage(content="You are a creative writer tasked with developing lore concepts for magical creatures in a game world."),
            HumanMessage(content=prompt)
        ]

        response = self.chatbot.invoke(messages)
        return response.content.strip()

    def generate_lore_outline(self, lore_aspect, concept, lore_focus):
        prompt = f"""
        Create an outline for the lore of {lore_aspect}, based on the following concept:
        {concept}

        Focus on the following aspects: {', '.join(lore_focus)}

        Provide an outline with 5-7 main sections, each with 2-3 subsections. Use the following format:
        1. Main Section Title
           1.1 Subsection
           1.2 Subsection
        2. Main Section Title
           2.1 Subsection
           2.2 Subsection
        ...
        """

        messages = [
            SystemMessage(content="You are a creative writer tasked with developing detailed outlines for magical creature lore in a game world."),
            HumanMessage(content=prompt)
        ]

        response = self.chatbot.invoke(messages)
        return response.content.strip()

    def generate_section_summaries(self, lore_aspect, outline, lore_focus):
        prompt = f"""
        Based on the following outline for {lore_aspect}, generate brief summaries for each main section:
        {outline}

        Focus on the following aspects: {', '.join(lore_focus)}

        Provide a 2-3 sentence summary for each main section, capturing the key points and themes.
        """

        messages = [
            SystemMessage(content="You are a creative writer tasked with summarizing sections of lore for magical creatures in a game world."),
            HumanMessage(content=prompt)
        ]

        response = self.chatbot.invoke(messages)
        return response.content.strip()

    def generate_full_lore(self, lore_aspect, summaries, num_sections, birth_situation):
        prompt = f"""
        Expand the following summaries into a full, detailed lore for {lore_aspect}. 
        Consider the birth situation: {birth_situation}

        Summaries:
        {summaries}

        Generate {num_sections} detailed sections based on these summaries. Each section should be 2-3 paragraphs long, 
        rich in detail and world-building elements. Ensure continuity and coherence between sections, and incorporate 
        elements from the birth situation where relevant.
        """

        messages = [
            SystemMessage(content="You are a creative writer tasked with developing extensive, detailed lore for magical creatures in a game world."),
            HumanMessage(content=prompt)
        ]

        response = self.chatbot.invoke(messages)
        return response.content.strip()

    def save_echo_to_json(self, echo_data):
        echo_id = echo_data['echo_id']
        file_name = f"{echo_id}.json"
        file_path = os.path.join(self.lore_dir, file_name)
        
        with open(file_path, 'w') as f:
            json.dump(echo_data, f, indent=2)
        
        print(f"[DEBUG] Echo data saved to {file_path}")
                                            
