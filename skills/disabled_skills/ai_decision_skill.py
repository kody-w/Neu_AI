from skills.basic_skill import BasicSkill
from colorama import Fore, Style
import json
from openai import AzureOpenAI

class AIArgumentAnalysisSkill(BasicSkill):
    def __init__(self):
        self.name = "AIArgumentAnalysis"
        self.metadata = {
            "name": self.name,
            "description": "Analyzes a question or topic from two perspectives and provides a final decision or conclusion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The main question or topic to be analyzed"
                    },
                    "perspective1": {
                        "type": "string",
                        "description": "The name or description of the first perspective"
                    },
                    "perspective2": {
                        "type": "string",
                        "description": "The name or description of the second perspective"
                    },
                    "rounds": {
                        "type": "integer",
                        "description": "The number of rounds for each perspective to present arguments"
                    }
                },
                "required": ["question", "perspective1", "perspective2", "rounds"]
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

    def perform(self, question, perspective1, perspective2, rounds):
        analysis = ArgumentAnalysis(self.client, question)
        
        analysis_log = [f"Question: {question}\n"]

        for round in range(1, rounds + 1):
            for perspective in [perspective1, perspective2]:
                response = analysis.get_perspective(perspective, round)
                
                color = Fore.RED if perspective == perspective1 else Fore.BLUE
                analysis_log.append(f"{color}{perspective} (Round {round}): {response}{Style.RESET_ALL}")

        final_decision = analysis.get_final_decision()
        analysis_log.append(f"\n{Fore.GREEN}Final Decision: {final_decision}{Style.RESET_ALL}")

        return "\n".join(analysis_log)

class ArgumentAnalysis:
    def __init__(self, client, question):
        self.question = question
        self.messages = [{"role": "system", "content": f"You are an AI tasked with analyzing the following question from multiple perspectives: {question}"}]
        self.client = client
        
    def get_perspective(self, perspective: str, round: int) -> str:
        if round == 1:
            prompt = f"Present the initial argument for the '{perspective}' perspective on the question: {self.question}"
        else:
            prompt = f"Continue the argument for the '{perspective}' perspective, considering previous points made."

        self.messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.messages,
            temperature=0.7,
            max_tokens=300,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        if response.choices:
            argument = response.choices[0].message.content.strip()
            self.messages.append({"role": "assistant", "content": argument})
            return argument
        else:
            return "Error in generating response"

    def get_final_decision(self):
        prompt = f"Based on the arguments presented for both perspectives, provide a final decision or conclusion on the question: {self.question}. Consider the strengths and weaknesses of each argument in your analysis."
        self.messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.messages,
            temperature=0.7,
            max_tokens=400,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        if response.choices:
            return response.choices[0].message.content.strip()
        else:
            return "Unable to reach a final decision."