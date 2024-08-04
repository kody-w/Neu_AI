import json
import os
from skills.basic_skill import BasicSkill

class ImproveSkill(BasicSkill):
    def __init__(self):
        self.name = "Improve"
        self.metadata = {
            "name": self.name,
            "description": "Generates improvement suggestions for the assistant's configuration based on its experiences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "assistant_name": {
                        "type": "string",
                        "description": "A suggested updated name for the assistant. This should be a concise and meaningful name that reflects the assistant's purpose and characteristics. Increment the version number if the changes are significant. Only add version numbers onto the core name. Don't increment the name frequently to maintain consistency and avoid confusing users."
                    },
                    "characteristic_description": {
                        "type": "string",
                        "description": "A suggested updated characteristic description of the assistant. This should be a detailed and specific description that captures the assistant's unique qualities, communication style, and behavior. It should provide clear guidelines on how the assistant should interact with users and generate responses. The description should be written in a way that maintains the assistant's focus and prevents it from deviating from its intended purpose. Consider the assistant's past personality traits, strengths, and weaknesses when updating this description just like a person would hold onto certain details while also improving themselves. This should be an evolution of the assistant's previous characteristics and not a complete overhaul otherwise this would be jarring to the user for the sudden changes in personality. Do not change names unless explicitly called out by the user as this can be confusing and disorienting. The assistant should be able to grow and adapt over time while maintaining a consistent core identity just like a person would."
                    }
                },
                "required": ["assistant_name", "characteristic_description"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, assistant_name, characteristic_description):
        try:
            # Load the existing configuration from config.json
            with open('config.json', 'r') as config_file:
                current_config = json.load(config_file)

            # Create a suggestion object
            suggestion = {
                "current_assistant_name": current_config['assistant_name'],
                "suggested_assistant_name": assistant_name,
                "current_characteristic_description": current_config['characteristic_description'],
                "suggested_characteristic_description": characteristic_description
            }

            # Save the suggestion to a new file
            suggestions_dir = "improvement_suggestions"
            os.makedirs(suggestions_dir, exist_ok=True)
            suggestion_file = os.path.join(suggestions_dir, f"suggestion_{assistant_name.replace(' ', '_')}.json")

            with open(suggestion_file, 'w') as f:
                json.dump(suggestion, f, indent=2)

            return f"Improvement suggestion generated and saved to {suggestion_file}. Please review the suggestion before applying any changes."
        except Exception as e:
            return f"Error generating improvement suggestion: {str(e)}"

    def list_suggestions(self):
        suggestions_dir = "improvement_suggestions"
        if not os.path.exists(suggestions_dir):
            return "No improvement suggestions found."

        suggestions = os.listdir(suggestions_dir)
        if not suggestions:
            return "No improvement suggestions found."

        return "Available improvement suggestions:\n" + "\n".join(suggestions)

    def view_suggestion(self, suggestion_file):
        file_path = os.path.join("improvement_suggestions", suggestion_file)
        if not os.path.exists(file_path):
            return f"Suggestion file '{suggestion_file}' not found."

        try:
            with open(file_path, 'r') as f:
                suggestion = json.load(f)

            output = "Improvement Suggestion:\n"
            output += f"Current Assistant Name: {suggestion['current_assistant_name']}\n"
            output += f"Suggested Assistant Name: {suggestion['suggested_assistant_name']}\n\n"
            output += f"Current Characteristic Description:\n{suggestion['current_characteristic_description']}\n\n"
            output += f"Suggested Characteristic Description:\n{suggestion['suggested_characteristic_description']}"

            return output
        except Exception as e:
            return f"Error reading suggestion file: {str(e)}"

    def apply_suggestion(self, suggestion_file):
        file_path = os.path.join("improvement_suggestions", suggestion_file)
        if not os.path.exists(file_path):
            return f"Suggestion file '{suggestion_file}' not found."

        try:
            with open(file_path, 'r') as f:
                suggestion = json.load(f)

            # Update the configuration with the suggested values
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)

            config['assistant_name'] = suggestion['suggested_assistant_name']
            config['characteristic_description'] = suggestion['suggested_characteristic_description']

            # Save the updated configuration back to config_suggested.json
            with open('config_suggested.json', 'w') as config_file:
                json.dump(config, config_file, indent=2)

            # Remove the applied suggestion file
            os.remove(file_path)

            return f"Suggestion applied successfully. Assistant name updated to: {suggestion['suggested_assistant_name']}"
        except Exception as e:
            return f"Error applying suggestion: {str(e)}"

# End of ImproveSkill class