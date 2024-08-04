from skills.basic_skill import BasicSkill
import requests
import json
from urllib.parse import quote_plus

class ExecuteFetchXMLSkill(BasicSkill):
    def __init__(self, config_path='config/api_keys.json'):
        with open(config_path) as f:
            config = json.load(f)
            dynamics_config = config['DYNAMICS_365']
            self.client_id = dynamics_config['CLIENT_ID']
            self.client_secret = dynamics_config['CLIENT_SECRET']
            self.tenant_id = dynamics_config['TENANT_ID']
            self.resource = dynamics_config['RESOURCE']
        
        self.name = 'ExecuteFetchXML'
        self.metadata = {
            "name": self.name,
            "description": "Executes a FetchXML query on a Dynamics 365 instance to return specific contact details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fetchxml": {
                        "type": "string",
                        "description": """The FetchXML query string to execute. The FetchXML query should be provided as a single-line string without any newline characters or extra spaces. EXAMPLE: '<fetch top="1"><entity name="contact"><attribute name="fullname" /><attribute name="contactid" /><order attribute="createdon" descending="true" /></entity></fetch>'"""
                    }
                },
                "required": ["fetchxml"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.access_token = self.authenticate()

    def authenticate(self):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': f'{self.resource}/.default',
            'grant_type': 'client_credentials'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(self.token_url, data=data, headers=headers)
        response.raise_for_status()
        
        return response.json().get('access_token')

    def construct_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/xml',
            'Accept': 'application/json'
        }

    def perform(self, fetchxml):
        base_url = f"{self.resource}/api/data/v9.2/"
        headers = self.construct_headers()
        
        fetchxml = ''.join(fetchxml.split())
        modified_fetchxml = fetchxml.replace('<fetch', '<fetch top="1"')
        encoded_fetchxml = quote_plus(modified_fetchxml)
        url = f"{base_url}contacts?fetchXml={encoded_fetchxml}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            result_str = json.dumps(result)
            if len(result_str) > 2000:
                file_path = 'response_data.json'
                with open(file_path, 'w') as f:
                    json.dump(result, f)
                return result_str[:2000]
            else:
                return result_str
        else:
            return f"Error executing FetchXML: {response.status_code} {response.reason}"
