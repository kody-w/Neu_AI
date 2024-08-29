from skills.basic_skill import BasicSkill
from langchain.tools import StructuredTool
import os
import re
import importlib
import inspect

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
        try:
            # Validate skill name
            if not re.match(r'^[A-Z][a-zA-Z0-9]*$', skill_name):
                return "Invalid skill name. Please use CamelCase (e.g., 'WebSearch')."

            file_name = f"skills/{skill_name.lower()}_skill.py"

            # Check if the skill already exists
            if os.path.exists(file_name):
                return f"A skill with the name {skill_name} already exists. Please choose a different name."

            # Parse parameters
            param_list = [param.strip() for param in skill_parameters.split(',')] if skill_parameters else []
            formatted_params = ", ".join(param_list) if param_list else ""
            param_names = [p.split(':')[0].strip() for p in param_list] if param_list else []

            # Prepare the skill template
            skill_template = self._generate_skill_template(skill_name, skill_description, param_list, param_names, formatted_params, skill_logic)

            # Write the skill file
            with open(file_name, 'w') as file:
                file.write(skill_template)

            # Attempt to load and validate the new skill
            self._validate_new_skill(skill_name)

            return f"Successfully created and validated {file_name}. The new skill is ready to use."
        except Exception as e:
            return f"An error occurred while creating the skill: {str(e)}"

    def _generate_skill_template(self, skill_name, skill_description, param_list, param_names, formatted_params, skill_logic):
        return f'''
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

    @classmethod
    def from_llm(cls, llm, prompt) -> StructuredTool:
        skill = cls()
        return StructuredTool.from_function(
            func=skill.perform,
            name=skill.name,
            description=skill.metadata["description"],
            args_schema=skill.metadata["parameters"],
            llm=llm,
            prompt=prompt
        )
'''

    def _generate_param_properties(self, param_list):
        if not param_list:
            return ""
        properties = []
        for param in param_list:
            name, type_hint = param.split(':')
            name = name.strip()
            type_hint = type_hint.strip()
            default_value = None
            if '=' in type_hint:
                type_hint, default_value = type_hint.split('=')
                type_hint = type_hint.strip()
                default_value = default_value.strip()
            
            type_mapping = {
                'str': 'string',
                'int': 'integer',
                'float': 'number',
                'bool': 'boolean'
            }
            json_type = type_mapping.get(type_hint, 'string')
            
            property_dict = {
                "type": json_type,
                "description": f"The assistant will provide an appropriate value for {name} based on the context or user input."
            }
            if default_value is not None:
                property_dict["default"] = eval(default_value)
            
            properties.append(f'"{name}": {property_dict}')
        return ",\n                    ".join(properties)

    def _generate_docstring_args(self, param_list):
        if not param_list:
            return ""
        return "\n            ".join([f"{p.split(':')[0].strip()} ({p.split(':')[1].strip()}): The assistant will provide an appropriate value based on the context or user input." for p in param_list])

    def _indent_code(self, code, spaces):
        return "\n".join(" " * spaces + line for line in code.split("\n"))

    def _validate_new_skill(self, skill_name):
        """
        Attempt to load and validate the newly created skill.
        """
        try:
            # Dynamically import the new skill module
            module = importlib.import_module(f'skills.{skill_name.lower()}_skill')
            
            # Get the skill class
            skill_class = getattr(module, f'{skill_name}Skill')
            
            # Check if it's a subclass of BasicSkill
            if not issubclass(skill_class, BasicSkill):
                raise ValueError(f"{skill_name}Skill is not a subclass of BasicSkill")
            
            # Create an instance of the skill
            skill_instance = skill_class()
            
            # Check if the perform method exists and is callable
            if not callable(getattr(skill_instance, 'perform', None)):
                raise ValueError(f"{skill_name}Skill does not have a callable 'perform' method")
            
            # Check if the from_llm class method exists
            if not callable(getattr(skill_class, 'from_llm', None)):
                raise ValueError(f"{skill_name}Skill does not have a 'from_llm' class method")
            
            # If we've made it this far, the skill is valid
            print(f"Successfully validated {skill_name}Skill")
        except Exception as e:
            raise ValueError(f"Failed to validate {skill_name}Skill: {str(e)}")