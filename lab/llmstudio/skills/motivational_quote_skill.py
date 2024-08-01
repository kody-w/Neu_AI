from skills.basic_skill import BasicSkill
import requests
import json

class MotivationalQuoteSkill(BasicSkill):
    def __init__(self):
        self.name = "get_motivational_quote"
        self.metadata = {
            "name": self.name,
            "description": "Get a motivational quote",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self):
        try:
            response = requests.get("https://api.quotable.io/random?tags=inspirational")
            data = response.json()
            quote = data['content']
            author = data['author']
            return json.dumps({"quote": quote, "author": author})
        except Exception as e:
            return json.dumps({"error": f"Error fetching quote: {str(e)}"})