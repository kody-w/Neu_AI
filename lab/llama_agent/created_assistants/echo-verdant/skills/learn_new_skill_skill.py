from skills.basic_skill import BasicSkill
from langchain.tools import StructuredTool
import os
import re

class LearnNewSkillSkill(BasicSkill):
    def __init__(self):
        self.name = "LearnNewSkill"
        self.metadata = {
            "name": self.name,
            "description": "Creates a new Python file for a specified skill, implementing it with best practices and integrating it into the assistant's framework. The assistant can provide appropriate parameter values based on user input or its best judgment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "The name of the new skill (use CamelCase, e.g., 'WebSearch')"
                    },
                    "skill_description": {
                        "type": "string",
                        "description": "A brief description of what the skill does"
                    },
                    "skill_parameters": {
                        "type": "string",
                        "description": "A comma-separated list of parameters the skill needs, e.g., 'query: str, limit: int = 5'"
                    },
                    "skill_logic": {
                        "type": "string",
                        "description": "The main logic of the skill, written as Python code"
                    }
                },
                "required": ["skill_name", "skill_description", "skill_parameters", "skill_logic"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, skill_name: str, skill_description: str, skill_parameters: str, skill_logic: str) -> str:
        """
        Create a new Python file for a specified skill with improved structure and error handling.

        Args:
            skill_name (str): The name of the new skill.
            skill_description (str): A brief description of what the skill does.
            skill_parameters (str): A comma-separated list of parameters the skill needs.
            skill_logic (str): The main logic of the skill, written as Python code.

        Returns:
            str: A message indicating the result of the operation.
        """
        # Validate skill name
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', skill_name):
            return "Invalid skill name. Please use CamelCase (e.g., 'WebSearch')."

        file_name = f"skills/{skill_name.lower()}_skill.py"
        
        # Parse parameters
        param_list = [param.strip() for param in skill_parameters.split(',')] if skill_parameters else []
        formatted_params = ", ".join(param_list) if param_list else ""
        param_names = [p.split(':')[0].strip() for p in param_list] if param_list else []
        
        # Prepare the skill template
        skill_template = f'''
from skills.basic_skill import BasicSkill
from langchain.tools import StructuredTool

class {skill_name}Skill(BasicSkill):
    def __init__(self):
        self.name = "{skill_name}"
        self.metadata = {{
            "name": self.name,
            "description": "{skill_description}",
            "parameters": {{
                "type": "object",
                "properties": {{
                    {self._generate_param_properties(param_list)}
                }},
                "required": {param_names}
            }}
        }}
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self{", " + formatted_params if formatted_params else ""}) -> str:
        """
        {skill_description}

        {"Args:" if param_list else ""}
            {self._generate_docstring_args(param_list)}

        Returns:
            str: The result of the skill operation.
        """
        try:
{self._indent_code(skill_logic, 12)}
        except Exception as e:
            return f"An error occurred while executing the {skill_name} skill: {{str(e)}}"
'''

        try:
            with open(file_name, 'w') as file:
                file.write(skill_template)
            return f"Successfully created {file_name}. You may need to restart the application to use this new skill."
        except Exception as e:
            return f"Error creating {file_name}: {str(e)}"

    def _generate_param_properties(self, param_list):
        if not param_list:
            return ""
        properties = []
        for param in param_list:
            name, type_hint = param.split(':')
            name = name.strip()
            type_hint = type_hint.strip()
            properties.append(f'"{name}": {{"type": "string", "description": "The assistant will provide an appropriate value for {name} based on the context or user input."}}')
        return ",\n                    ".join(properties)

    def _generate_docstring_args(self, param_list):
        if not param_list:
            return ""
        return "\n            ".join([f"{p.split(':')[0].strip()} ({p.split(':')[1].strip()}): The assistant will provide an appropriate value based on the context or user input." for p in param_list])

    def _indent_code(self, code, spaces):
        return "\n".join(" " * spaces + line for line in code.split("\n"))