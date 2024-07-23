from skills.basic_skill import BasicSkill
import os
import json
import requests
from time import sleep
from datetime import datetime

class StoryGeneratorSkill(BasicSkill):
    def __init__(self):
        self.name = "StoryGenerator"
        self.metadata = {
            "name": self.name,
            "description": "Generates a complete story using Azure OpenAI's API, following a multi-step process, and saves each stage to separate files. All aspects of the generation process are customizable through parameters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "genre": {
                        "type": "string",
                        "description": "The genre of the story to generate (e.g., 'fantasy', 'sci-fi', 'mystery')"
                    },
                    "idea": {
                        "type": "string",
                        "description": "The initial story idea or prompt to inspire the generation"
                    },
                    "num_chapters": {
                        "type": "integer",
                        "description": "Number of chapters to generate in the full story",
                        "default": 7
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Controls randomness in generation. Higher values (e.g., 0.8) make output more random, lower values (e.g., 0.2) make it more focused and deterministic",
                        "default": 0.7
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "The maximum number of tokens to generate in each API call. Adjust based on desired length of responses",
                        "default": 2000
                    },
                    "top_p": {
                        "type": "number",
                        "description": "An alternative to sampling with temperature, called nucleus sampling. Set between 0 and 1",
                        "default": 0.95
                    },
                    "frequency_penalty": {
                        "type": "number",
                        "description": "Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim",
                        "default": 0.2
                    },
                    "presence_penalty": {
                        "type": "number",
                        "description": "Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics",
                        "default": 0.0
                    },
                    "model": {
                        "type": "string",
                        "description": "The name of the Azure OpenAI model to use (e.g., 'gpt-4o', 'gpt-35-turbo')",
                        "default": "gpt-4o"
                    }
                },
                "required": ["genre", "idea"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        # Load API configuration
        self.load_api_config()
        
        # Ensure the stories directory exists
        self.stories_dir = os.path.join(os.getcwd(), 'generated_stories')
        os.makedirs(self.stories_dir, exist_ok=True)

    def load_api_config(self):
        try:
            with open('config/api_keys.json', 'r') as api_keys_file:
                api_keys = json.load(api_keys_file)
            
            self.api_key = api_keys['azure_openai_api_key']
            self.api_version = api_keys['azure_openai_api_version']
            self.endpoint = f"{api_keys['azure_openai_endpoint']}openai/deployments/"
        except FileNotFoundError:
            raise Exception("API configuration file not found. Please ensure 'config/api_keys.json' exists with the necessary Azure OpenAI details.")

    def perform(self, genre, idea, num_chapters=7, temperature=0.7, max_tokens=2000, top_p=0.95, frequency_penalty=0.2, presence_penalty=0.0, model="gpt-4o"):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            story_dir = os.path.join(self.stories_dir, f"{genre.lower().replace(' ', '_')}_{timestamp}")
            os.makedirs(story_dir, exist_ok=True)

            # Generate and save story idea
            story_idea = self.generate_story_idea(genre, idea, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model)
            idea_file = self.save_to_file(story_dir, "1_story_idea.txt", story_idea)
            
            # Generate and save story outline
            story_outline = self.generate_story_outline(genre, idea_file, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model)
            outline_file = self.save_to_file(story_dir, "2_story_outline.txt", story_outline)
            
            # Generate and save chapter summaries
            chapter_summaries = self.generate_chapter_summaries(genre, outline_file, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model)
            summaries_file = self.save_to_file(story_dir, "3_chapter_summaries.txt", chapter_summaries)
            
            # Generate and save full story
            full_story = self.generate_full_story(genre, summaries_file, num_chapters, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model)
            story_file = self.save_to_file(story_dir, "4_full_story.txt", full_story)
            
            return f"Story successfully generated and saved in {story_dir}"
        except Exception as e:
            return f"An error occurred while generating the story: {str(e)}"

    def azure_openai_call(self, messages, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model):
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
        }

        try:
            response = requests.post(f"{self.endpoint}{model}/chat/completions?api-version={self.api_version}", headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.RequestException as e:
            if "429" in str(e):
                sleep(20)  # Wait for 20 seconds before retrying
                return self.azure_openai_call(messages, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model)
            else:
                raise

    def generate_story_idea(self, genre, idea, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model):
        messages = [
            {"role": "system", "content": f"You are a {genre} author. Your task is to write {genre} stories in a vivid and intriguing language."},
            {"role": "user", "content": f"""
Fill out the following template for a {genre} story:
Title: [Insert story title here]
Setting: [Insert setting details here, including time period, location, and any relevant background information]
Main Plot: [Insert the main plot of the story]
Main Character1: [Insert protagonist's name, age, and occupation, as well as a brief description of their personality and motivations]
Main Character2: [Insert protagonist's name, age, and occupation, as well as a brief description of their personality and motivations]
Dialogue: [Instructions for using dialogue to advance the plot, reveal character, and provide information to the reader]
Theme: [Insert the central theme of the story and instructions for developing it throughout the plot, character, and setting]
Tone: [Insert the desired tone for the story and instructions for maintaining consistency and appropriateness to the setting and characters]
Pacing: [Instructions for varying the pace of the story to build and release tension, advance the plot, and create dramatic effect]
Additional Details: [Insert any additional details or requirements for the story]

Use the following idea as inspiration: {idea}

FILL OUT THE TEMPLATE ABOVE FOR A {genre} STORY:
"""}
        ]
        return self.azure_openai_call(messages, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model)

    def generate_story_outline(self, genre, idea_file, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model):
        with open(idea_file, 'r', encoding='utf-8') as file:
            story_idea = file.read()

        messages = [
            {"role": "system", "content": f"You are a {genre} author. Your task is to write {genre} stories in a vivid and intriguing language, always focus on a show dont tell writing style and include intriguing Dialog."},
            {"role": "user", "content": f"""
Write a 7 chapter detailed outline for the story from the following factors:
{story_idea}
WRITE A 7 CHAPTER DETAILED OUTLINE FOR THE STORY FROM FACTORS ABOVE:
"""}
        ]
        return self.azure_openai_call(messages, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model)

    def generate_chapter_summaries(self, genre, outline_file, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model):
        with open(outline_file, 'r', encoding='utf-8') as file:
            story_outline = file.read()

        messages = [
            {"role": "system", "content": f"You are a {genre} author. Your task is to write {genre} stories in a vivid and intriguing language."},
            {"role": "user", "content": f"""
Write 7 detailed story chapters summaries from the following outlines:
{story_outline}
WRITE 7 DETAILED STORY CHAPTERS SUMMARIES FROM THE OUTLINES ABOVE:
"""}
        ]
        return self.azure_openai_call(messages, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model)

    def generate_full_story(self, genre, summaries_file, num_chapters, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model):
        with open(summaries_file, 'r', encoding='utf-8') as file:
            chapter_summaries = file.read()

        full_story = ""
        for chapter in range(1, num_chapters + 1):
            messages = [
                {"role": "system", "content": f"You are a {genre} author. Your task is to write {genre} stories in a vivid and intriguing language."},
                {"role": "user", "content": f"""
Write Chapter {chapter} in great detail and in a vivid and intriguing language from the following information:
{chapter_summaries}
WRITE CHAPTER {chapter} IN GREAT DETAIL AND IN A VIVID AND INTRIGUING LANGUAGE FROM THE INFORMATION ABOVE:
"""}
            ]
            chapter_content = self.azure_openai_call(messages, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, model)
            full_story += f"Chapter {chapter}\n\n{chapter_content}\n\n"
        
        return full_story

    def save_to_file(self, directory, filename, content):
        file_path = os.path.join(directory, filename)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return file_path