from skills.basic_skill import BasicSkill
from colorama import Fore, Style
import os
import json
from openai import AzureOpenAI

class AIDebateSkill(BasicSkill):
    def __init__(self):
        self.name = "AIDebate"
        self.metadata = {
            "name": self.name,
            "description": "Facilitates an AI-driven debate between two personas on a given topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic of the debate"
                    },
                    "tone": {
                        "type": "string",
                        "description": "The tone of the debate (e.g., 'Heated Discussion', 'Friendly', 'Academic')"
                    },
                    "persona1": {
                        "type": "string",
                        "description": "The name of the first debater"
                    },
                    "persona2": {
                        "type": "string",
                        "description": "The name of the second debater"
                    },
                    "rounds": {
                        "type": "integer",
                        "description": "The number of rounds for the debate"
                    }
                },
                "required": ["topic", "tone", "persona1", "persona2", "rounds"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        # Load API configuration
        with open('config/api_keys.json', 'r') as api_keys_file:
            api_keys = json.load(api_keys_file)

        self.client = AzureOpenAI(
            api_key=api_keys['azure_openai_api_key'],
            api_version=api_keys['azure_openai_api_version'],
            azure_endpoint=api_keys['azure_openai_endpoint']
        )

    def perform(self, topic, tone, persona1, persona2, rounds):
        debate = DiscussGPT(self.client)
        debate.set_topic(topic)
        debate.set_tone(tone)

        debate_log = []

        for round in range(1, rounds + 1):
            for persona in [persona1, persona2]:
                debate.switch_persona(persona)
                question = "What's your take on this?" if round == 1 else "Your response?"
                response = debate.chat(question)
                
                color = Fore.RED if persona == persona1 else Fore.BLUE
                debate_log.append(f"{color}{persona}: {response}{Style.RESET_ALL}")

        winner = debate.judge_winner()
        debate_log.append(f"{Fore.GREEN}The winner of the debate is: {winner}{Style.RESET_ALL}")

        return "\n".join(debate_log)

class DiscussGPT:
    def __init__(self, client):
        self.topic = "General"
        self.tone = "Neutral"
        self.current_persona = "Default"
        self.messages = []
        self.client = client
        
    def set_topic(self, topic: str):
        self.topic = topic
    
    def set_tone(self, tone: str):
        self.tone = tone
    
    def switch_persona(self, persona: str):
        self.current_persona = persona

    def chat(self, user_input: str) -> str:
        system_message = f"You are now a chatbot with the persona of {self.current_persona}. The topic is {self.topic}. The tone of the discussion should be {self.tone}."
        self.messages.append({"role": "system", "content": system_message})
        self.messages.append({"role": "user", "content": user_input})
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages,
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        if response.choices:
            chat_output = response.choices[0].message.content.strip()
            self.messages.append({"role": "assistant", "content": chat_output})
            return chat_output
        else:
            return "Error in generating response"

    def judge_winner(self):
        judging_criteria = f"Based on the arguments provided, who won the debate between {self.messages[0]['content']} and {self.messages[2]['content']}? You are a debate coach. You have to choose a winner no matter how close they are in points. It is important to get this right."
        self.messages.append({"role": "user", "content": judging_criteria})
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages,
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        if response.choices:
            return response.choices[0].message.content.strip()
        else:
            return "Couldn't determine a winner."