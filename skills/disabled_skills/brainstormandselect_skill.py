
from skills.basic_skill import BasicSkill

class BrainstormAndSelectSkill(BasicSkill):
    def __init__(self):
        self.name = "BrainstormAndSelect"
        self.metadata = {
            "name": self.name,
            "description": "Allows for input on a topic, utilizes brainstorming by agents, selects the best option, and shares it back with the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The assistant will provide an appropriate value for topic based on the context or user input."}
                },
                "required": ['topic']
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, topic: str) -> str:
        """
        Allows for input on a topic, utilizes brainstorming by agents, selects the best option, and shares it back with the user.

        Args:
            topic (str): The assistant will provide an appropriate value based on the context or user input.

        Returns:
            str: The result of the skill operation.
        """
        try:
            import openai
            class BrainstormAndSelectSkill(BaseSkill):
                def __init__(self, api_key):
                    self.api_key = api_key
            
                def brainstorm_and_select(self, topic: str) -> str:
                    openai.api_key = self.api_key
            
                    # Define brainstorming prompt for agents
                    brainstorming_prompt = f'Brainstorm the coolest, most mind-blowing, out of the box ChatGPT prompts that will really show off the power of ChatGPT on the topic: {topic}'
                    
                    # Get brainstorming responses from agents
                    responses = [openai.Completion.create(
                        model="text-davinci-003",
                        prompt=brainstorming_prompt,
                        max_tokens=150
                    ) for _ in range(10)]
            
                    # Extract text responses from agents
                    options = [response['choices'][0]['text'].strip() for response in responses]
            
                    # Define selection prompt
                    selection_prompt = f'Select the best option from the following brainstorming options: {options}'
            
                    # Get the selected best option
                    best_option = openai.Completion.create(
                        model="text-davinci-003",
                        prompt=selection_prompt,
                        max_tokens=50
                    )
            
                    return best_option['choices'][0]['text'].strip()
            
                def main(self, topic: str) -> str:
                    return self.brainstorm_and_select(topic)
            
            
        except Exception as e:
            return f"An error occurred while executing the BrainstormAndSelect skill: {str(e)}"
