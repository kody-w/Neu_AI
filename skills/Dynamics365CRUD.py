import requests
import json
from urllib.parse import quote_plus
from skills.basic_skill import BasicSkill

class Dynamics365CRUDSkill(BasicSkill):
    def __init__(self, config_path='config/api_keys.json'):
        # Load configuration from the given JSON file path
        with open(config_path) as f:
            config = json.load(f)
            dynamics_config = config['DYNAMICS_365']
            self.client_id = dynamics_config['CLIENT_ID']
            self.client_secret = dynamics_config['CLIENT_SECRET']
            self.tenant_id = dynamics_config['TENANT_ID']
            self.resource = dynamics_config['RESOURCE']
        
        # Metadata setup
        self.name = "Dynamics365CRUD"
        self.metadata = {
            "name": self.name,
            "description": "Performs CRUD operations with Dynamics 365 Web API. ",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The CRUD operation to perform. Must be one of: create, read, update, delete."
                    },
                    "entity": {
                        "type": "string",
                        "description": "The entity to perform the operation on. Examples: accounts, contacts, leads, and custom entities like kjw_managelistsofaicoworkers"
                    },
                    "data": {
                        "type": "string",
                        "description": "Data for create and update operations. JSON format expected.",
                        "optional": True
                    },
                    "fetchxml": {
                        "type": "string",
                        "description": 'Completed FetchXML query for complex data retrieval for Dynamics 365 Web API. ALWAYS Include around 4 - 6 columns only and not the whole record. You should only return top 1 for records to reduce payload. You can declare what columns you want returned within the fetchxml syntax. Here is an example of what will be given: <fetch top="1" > <entity name="account" > <attribute name="name" /> <attribute name="primarycontactid" /> <attribute name="telephone1" /> <order attribute="name" descending="false" /> </entity> </fetch> When executing a search with the Dynamics365 search skill, specifically through Dynamics365CRUD, you can ensure it only returns the first record by setting the `top` attribute within your FetchXML query to "1". This limits the result set to the first record only. Here\'s an example snippet for clarity: ```xml ``` By setting ``, the query targets just the top record matching your criteria. This way, the return is concise, making your retrieval operation efficient.',
                        "optional": True
                    }
                    
                },
                "required": ["operation", "entity", "fetchxml"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.access_token = self.authenticate()

    def authenticate(self):
        # Prepare data for the token request
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': f'{self.resource}/.default',
            'grant_type': 'client_credentials'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        # Make the token request
        response = requests.post(self.token_url, data=data, headers=headers)
        response.raise_for_status()  # Raises stored HTTPError, if one occurred
        
        # Extract the access token from response
        return response.json().get('access_token')

    def construct_headers(self):
        # Headers required for making requests to Dynamics 365 Web API
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0',
            'Accept': 'application/json'
        }

    def perform(self, operation, entity, data=None, fetchxml=None, fetchxml_entity_columns_to_return_in_query_results=None):
        base_url = f"{self.resource}/api/data/v9.2/"
        headers = self.construct_headers()

        if operation == "create":
            url = f"{base_url}{entity}"
            response = requests.post(url, headers=headers, data=data)
        elif operation == "read":
            url = f"{base_url}{entity}"
            response = requests.get(url, headers=headers)
        elif operation == "update":
            url = f"{base_url}{entity}"
            response = requests.patch(url, headers=headers, data=data)
        elif operation == "delete":
            url = f"{base_url}{entity}"
            response = requests.delete(url, headers=headers)
        elif operation == "query" and fetchxml:
            # Modify the FetchXML query to return only the top 1 record
            modified_fetchxml = fetchxml.replace('<fetch', '<fetch top="1"')
            
            # If no specific columns are specified, return only the default name field
            if not fetchxml_entity_columns_to_return_in_query_results:
                entity_name = entity.replace('set', '')  # Remove 'set' from entity name if present
                default_field = f'<attribute name="{entity_name}name" />'
                modified_fetchxml = modified_fetchxml.replace('</entity>', f'{default_field}</entity>')
            
            encoded_fetchxml = quote_plus(modified_fetchxml)
            url = f"{base_url}{entity}?fetchXml={encoded_fetchxml}"
            response = requests.get(url, headers=headers)
        else:
            raise ValueError("Unsupported operation or missing fetchxml for query.")

        result = response.json() if response.content else "Operation successful."
        
        # Ensure the result string does not exceed 2000 characters
        result_str = json.dumps(result)
        if len(result_str) > 2000:

        # Save the full response to a file
            file_path = 'response_data.json'
            with open(file_path, 'w') as f:
                json.dump(result, f)

            return result_str[:2000]
        else:
            return result_str