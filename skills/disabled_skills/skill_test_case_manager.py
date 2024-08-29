from skills.basic_skill import BasicSkill
import json
import os

class SkillTestCaseManagerSkill(BasicSkill):
    def __init__(self):
        self.name = "SkillTestCaseManager"
        self.metadata = {
            "name": self.name,
            "description": "Manages test cases for skills. This skill allows you to save, run, list, and delete test cases for various skills. Each test case consists of a skill name, a test case name, and the input that would be provided to that skill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The action to perform. Must be one of the following:\n- 'save': Save a new test case or update an existing one.\n- 'run': Retrieve the input for a specific test case.\n- 'list': Show all test cases for a specific skill.\n- 'delete': Remove a specific test case."
                    },
                    "skill_name": {
                        "type": "string",
                        "description": "The name of the skill for which you're managing a test case. This should be the exact name of the skill as it's used in the system (e.g., 'AIArgumentAnalysisSkill', 'ImageGenerationSkill')."
                    },
                    "test_case_name": {
                        "type": "string",
                        "description": "A unique identifier for this test case. This is required for 'save', 'run', and 'delete' actions. For 'save', if a test case with this name already exists for the specified skill, it will be overwritten. For 'list', this parameter is ignored."
                    },
                    "test_input": {
                        "type": "string",
                        "description": "The input that would be provided to the skill for this test case. This is only required for the 'save' action and should be a string representing exactly what would be input to the skill when running this test case."
                    }
                },
                "required": ["action", "skill_name"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.test_cases_file = 'skill_test_cases.json'

    def perform(self, action, skill_name, test_case_name=None, test_input=None):
        if action == 'save':
            if not test_case_name or not test_input:
                return "Error: Both 'test_case_name' and 'test_input' are required for the 'save' action."
            return self.save_test_case(skill_name, test_case_name, test_input)
        elif action == 'run':
            if not test_case_name:
                return "Error: 'test_case_name' is required for the 'run' action."
            return self.run_test_case(skill_name, test_case_name)
        elif action == 'list':
            return self.list_test_cases(skill_name)
        elif action == 'delete':
            if not test_case_name:
                return "Error: 'test_case_name' is required for the 'delete' action."
            return self.delete_test_case(skill_name, test_case_name)
        else:
            return f"Invalid action: '{action}'. Please use 'save', 'run', 'list', or 'delete'."

    def save_test_case(self, skill_name, test_case_name, test_input):
        test_cases = self.load_test_cases()
        
        if skill_name not in test_cases:
            test_cases[skill_name] = {}
        
        test_cases[skill_name][test_case_name] = test_input
        
        self.save_test_cases(test_cases)
        return f"Test case '{test_case_name}' for skill '{skill_name}' saved successfully."

    def run_test_case(self, skill_name, test_case_name):
        test_cases = self.load_test_cases()
        
        if skill_name not in test_cases or test_case_name not in test_cases[skill_name]:
            return f"Error: Test case '{test_case_name}' for skill '{skill_name}' not found."
        
        test_input = test_cases[skill_name][test_case_name]
        
        return f"Test case '{test_case_name}' for skill '{skill_name}':\nInput: {test_input}"

    def list_test_cases(self, skill_name):
        test_cases = self.load_test_cases()
        
        if skill_name not in test_cases:
            return f"No test cases found for skill '{skill_name}'."
        
        return f"Test cases for skill '{skill_name}':\n" + "\n".join(test_cases[skill_name].keys())

    def delete_test_case(self, skill_name, test_case_name):
        test_cases = self.load_test_cases()
        
        if skill_name not in test_cases or test_case_name not in test_cases[skill_name]:
            return f"Error: Test case '{test_case_name}' for skill '{skill_name}' not found."
        
        del test_cases[skill_name][test_case_name]
        
        if not test_cases[skill_name]:
            del test_cases[skill_name]
        
        self.save_test_cases(test_cases)
        return f"Test case '{test_case_name}' for skill '{skill_name}' deleted successfully."

    def load_test_cases(self):
        if not os.path.exists(self.test_cases_file):
            return {}
        with open(self.test_cases_file, 'r') as f:
            return json.load(f)

    def save_test_cases(self, test_cases):
        with open(self.test_cases_file, 'w') as f:
            json.dump(test_cases, f, indent=2)