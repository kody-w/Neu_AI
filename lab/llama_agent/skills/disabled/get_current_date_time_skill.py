
from skills.basic_skill import BasicSkill
from langchain.tools import StructuredTool

class GetCurrentDateTimeSkill(BasicSkill):
    def __init__(self):
        self.name = "GetCurrentDateTime"
        self.metadata = {
            "name": self.name,
            "description": "A skill to retrieve the current date and time.",
            "parameters": {
                "type": "object",
                "properties": {
                    
                },
                "required": []
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self) -> str:
        """
        A skill to retrieve the current date and time.

        
            

        Returns:
            str: The result of the skill operation.
        """
        try:
            import datetime
            return datetime.datetime.now()
        except Exception as e:
            return f"An error occurred while executing the GetCurrentDateTime skill: {str(e)}"
