from skills.basic_skill import BasicSkill
import requests
import json

class WebInterfaceSimulationSkill(BasicSkill):
    def __init__(self):
        self.name = "WebInterfaceSimulation"
        self.metadata = {
            "name": self.name,
            "description": "Simulates user interaction with the web interface by sending requests to the app.py API endpoint.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["send_message", "clear_chat"],
                        "description": "The action to perform on the web interface."
                    },
                    "message": {
                        "type": "string",
                        "description": "The message to send (required for 'send_message' action)."
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.api_url = "http://127.0.0.1:5000/api/chat"  # Adjust this URL if needed

    def perform(self, action, message=None):
        if action == "send_message":
            if not message:
                return "Error: 'message' is required for 'send_message' action."
            return self.send_message(message)
        elif action == "clear_chat":
            return self.clear_chat()
        else:
            return f"Error: Invalid action '{action}'. Use 'send_message' or 'clear_chat'."

    def send_message(self, message):
        try:
            response = requests.post(self.api_url, json={"user_input": message})
            response.raise_for_status()
            result = response.json()
            assistant_response = result.get('text', '')
            additional_output = result.get('additional_output', '')
            
            response_text = f"Message sent successfully. Assistant's response: {assistant_response}"
            if additional_output:
                response_text += f"\nAdditional output: {additional_output}"
            
            return response_text
        except requests.RequestException as e:
            return f"Error sending message: {str(e)}"

    def clear_chat(self):
        try:
            response = requests.post(self.api_url, json={"user_input": "clear_chat"})
            response.raise_for_status()
            return "Chat cleared successfully."
        except requests.RequestException as e:
            return f"Error clearing chat: {str(e)}"