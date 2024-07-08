from skills.basic_skill import BasicSkill
import requests


class CallPowerAutomateFlowSkill(BasicSkill):
    def __init__(self):
        self.name = "CallPowerAutomateFlow"
        self.metadata = {
            "name": self.name,
            "description": "Calls a Microsoft Power Automate flow using the provided FetchXML query and returns the response.",
            "parameters": {
                "type": "object",
                "properties": {
                    "params": {
                        "type": "object",
                        "description": "The query parameters to include in the request."
                    },
                    "fetchxml": {
                        "type": "string",
                        "description": "The FetchXML query to include in the request body."
                    }
                },
                "required": ["fetchxml"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, fetchxml=None):
        try:
            url = "https://prod-164.westus.logic.azure.com:443/workflows/b880b64e2e67400ea18ba43cb16e38cb/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=uO9Ag3k0NGVpMuwjf7mRSaNw3Gy1uNh1YeUe6Oft8vc"  # Hardcoded Power Automate URL
            payload = {
                "fetchXml": fetchxml
            }
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post(url, json=payload, headers=headers)

            max_response_length = 1000  # Adjust this value as needed
            response_text = response.text
            if len(response_text) > max_response_length:
                response_text = response_text[:max_response_length] + "..."

            return f"Response Status: {response.status_code}, Response Body: {response_text}"
        except Exception as e:
            return f"An error occurred: {str(e)}"
