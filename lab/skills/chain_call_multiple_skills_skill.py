from skills.basic_skill import BasicSkill

class ChainCallMultipleSkillsSkill(BasicSkill):
    def __init__(self):
        self.name = "ChainCall"
        self.metadata = {
            "name": self.name,
            "description": "Dynamically chain skills based what you think is needed. Chains the calling of multiple skills based on user needs, ensuring a seamless interaction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skills_sequence": {
                        "type": "array",
                        "description": "An ordered list of skills and their parameters to be called.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "skill_name": {
                                    "type": "string",
                                    "description": "The name of the skill to call."
                                },
                                "parameters": {
                                    "type": "object",
                                    "description": "Parameters to pass to the skill.",
                                    "additionalProperties": True
                                }
                            },
                            "required": ["skill_name", "parameters"]
                        }
                    }
                },
                "required": ["skills_sequence"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, skills_sequence):
        results = []
        for skill in skills_sequence:
            skill_name = skill['skill_name']
            skill_parameters = skill.get('parameters', {})
            # Assume assistant has a method to call skills by name with parameters
            result = self.call_skill(skill_name, skill_parameters)
            results.append(result)
        return " -> ".join(results)

    def call_skill(self, skill_name, skill_parameters):
        # This method should dynamically call the skill based on skill_name and pass skill_parameters
        # Implementation depends on how skills are managed within the assistant framework
        # For demonstration, just return a placeholder string
        return f"Called {skill_name} with {skill_parameters}"
