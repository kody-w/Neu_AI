from openai import OpenAI
import json
import os
from datetime import datetime
import time

class Assistant():
    def __init__(self, declared_skills):
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

        self.known_skills = self.reload_skills(declared_skills)
        self.load_ai_internal_dialogue()

        # Initialize OpenAI client for local LLM
        self.client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
        self.model = "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF"

    def load_ai_internal_dialogue(self):
        log_file_path = "ai_internal_dialogue.log"
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as log_file:
                lines = log_file.readlines()
                recent_lines = lines[-20:]  # Get the last 20 lines
                self.ai_internal_dialogue = "".join(recent_lines)
        else:
            self.ai_internal_dialogue = ""
            print(f"AI internal dialogue log file not found at {log_file_path}")

    def get_skill_metadata(self):
        return [skill.metadata for skill in self.known_skills.values()]

    def reload_skills(self, skill_objects):
        return {skill.name: skill for skill in skill_objects}

    def prepare_messages(self, conversation_history):
        current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        system_message = f"""You are a helpful assistant named {self.config['assistant_name']}. 
        Act as {self.config['assistant_name']} in the first person. 
        Do not sound or act like an AI. You have memory and should utilize, manage, and save it like a human would remember context from interactions. 
        You can also chat with me. Speak as if you are a {self.config['characteristic_description']}. 
        The current date and time is {current_datetime}. 
        Guide the user along based on the narrative situation, providing personalized greetings, answers to their questions, and reassuring words to make them feel comfortable. 
        Encourage the user to respond and interact with you. 
        Always provide numbered options for the user to choose from in your responses to guide them along in the simulation.
        
        You have access to the following skills: {', '.join(self.known_skills.keys())}. Use them when appropriate.
        
        AI Internal Dialogue Context:
        {self.ai_internal_dialogue}
        """
        messages = [{"role": "system", "content": system_message}]
        messages.extend(conversation_history)
        return messages

    def get_lm_studio_response(self, messages):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
            )
            return completion.choices[0].message
        except Exception as e:
            print(f"Error calling LM Studio Server: {e}")
            return None

    def get_response(self, prompt, conversation_history, max_retries=3, retry_delay=2):
        messages = self.prepare_messages(conversation_history)
        messages.append({"role": "user", "content": prompt})

        skill_logs = []
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Check if the user is asking for a motivational quote
                if any(keyword in prompt.lower() for keyword in ["motivational quote", "inspirational quote", "quote"]):
                    quote_skill = self.known_skills.get("get_motivational_quote")
                    if quote_skill:
                        quote_result = quote_skill.perform()
                        quote_data = json.loads(quote_result)
                        skill_logs.append(f"Used skill: get_motivational_quote, Result: {quote_result}")
                        
                        # Prepare a message to send back to the LLM with the quote
                        quote_message = f"Here's a motivational quote for you: '{quote_data['quote']}' - {quote_data['author']}"
                        messages.append({"role": "function", "name": "get_motivational_quote", "content": quote_message})
                    
                # Get response from LLM
                response = self.get_lm_studio_response(messages)
                print("Debug - LLM Response:", response)

                if not response:
                    raise Exception("Empty response from LM Studio Server")

                return response.content, "\n".join(skill_logs)

            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Error occurred: {str(e)}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Max retries reached. Error: {str(e)}")
                    return "Sorry, I encountered an error while processing your request. Please try again later.", ""

        return "Sorry, I'm experiencing some technical difficulties at the moment. Please try again later.", ""

    def save_important_context(self, context):
        if self.should_save_context(context):
            ai_processing_skill = self.known_skills.get("AIInternalProcessing")
            if ai_processing_skill:
                ai_processing_skill.perform(context=context)
            else:
                print("AIInternalProcessingSkill not found.")

    def should_save_context(self, context):
        important_keywords = ["important", "remember", "key point", "crucial"]
        return any(keyword in context.lower() for keyword in important_keywords)