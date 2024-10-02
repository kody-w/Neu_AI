import requests
import json
import time
from urllib.parse import quote_plus
from skills.basic_skill import BasicSkill


class Dynamics365CRUDSkill(BasicSkill):
    def __init__(self, config_path='config/api_keys.json', max_retries=3, retry_delay=5):
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
                        "description": "The entity to perform the operation on. Examples: accounts, contacts, leads, and custom entities"
                    },
                    "data": {
                        "type": "string",
                        "description": "Data for create and update operations. JSON format expected."
                    },
                    "fetchxml": {
                        "type": "string",
                        "description": """The FetchXML query string to execute. The FetchXML query should be provided as a single-line string without any newline characters or extra spaces."""
                    },
                    "fetchxml_entity_columns_to_return_in_query_results": {
                        "type": "string",
                        "description": "The columns of the entity to return in the query results. If not specified, only the default name field will be returned."
                    }
                },
                "required": ["operation", "entity", "fetchxml", "fetchxml_entity_columns_to_return_in_query_results"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.access_token = self.authenticate()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

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

    def perform_with_retry(self, operation, entity, data=None, fetchxml=None, fetchxml_entity_columns_to_return_in_query_results=None):
        retries = 0
        while retries <= self.max_retries:
            try:
                return self.perform(operation, entity, data, fetchxml, fetchxml_entity_columns_to_return_in_query_results)
            except requests.exceptions.RequestException as e:
                if retries == self.max_retries:
                    raise e
                else:
                    print(f"Request failed. Retrying in {self.retry_delay} seconds... (Attempt {retries + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                    retries += 1

    def perform(self, operation, entity, data=None, fetchxml=None, fetchxml_entity_columns_to_return_in_query_results=None):
        base_url = f"{self.resource}/api/data/v9.2/"
        headers = self.construct_headers()

        print(f"Debug: Performing operation '{operation}' on entity '{entity}'")
        print(f"Debug: Data: {data}")
        print(f"Debug: FetchXML: {fetchxml}")
        print(f"Debug: FetchXML Entity Columns: {fetchxml_entity_columns_to_return_in_query_results}")

        if operation == "create":
            url = f"{base_url}{entity}"
            print(f"Debug: Create URL: {url}")
            print(f"Debug: Create Headers: {headers}")
            print(f"Debug: Create Data: {data}")
            response = requests.post(url, headers=headers, data=data)
        elif operation == "read":
            url = f"{base_url}{entity}"
            print(f"Debug: Read URL: {url}")
            print(f"Debug: Read Headers: {headers}")
            response = requests.get(url, headers=headers)
        elif operation == "update":
            url = f"{base_url}{entity}"
            print(f"Debug: Update URL: {url}")
            print(f"Debug: Update Headers: {headers}")
            print(f"Debug: Update Data: {data}")
            response = requests.patch(url, headers=headers, data=data)
        elif operation == "delete":
            url = f"{base_url}{entity}"
            print(f"Debug: Delete URL: {url}")
            print(f"Debug: Delete Headers: {headers}")
            response = requests.delete(url, headers=headers)
        elif operation == "query" and fetchxml:
            # Modify the FetchXML query to return only the top 1 record
            modified_fetchxml = fetchxml.replace('<fetch', '<fetch top="1"')

            encoded_fetchxml = quote_plus(modified_fetchxml)
            url = f"{base_url}{entity}?fetchXml={encoded_fetchxml}"
            print(f"Debug: Query URL: {url}")
            print(f"Debug: Query Headers: {headers}")
            response = requests.get(url, headers=headers)
        else:
            raise ValueError("Unsupported operation or missing fetchxml for query.")

        print(f"Debug: Response Status Code: {response.status_code}")
        print(f"Debug: Response Content: {response.content}")

        if response.status_code != 200:
            print(f"Error: Request failed with status code {response.status_code}")
            print(f"Error Details: {response.text}")
            raise Exception(f"Request failed with status code {response.status_code}")

        result = response.json() if response.content else "Operation successful."

        # Ensure the result string does not exceed 2000 characters
        result_str = json.dumps(result)
        if len(result_str) > 20000:
            # Save the full response to a file
            file_path = 'response_data.json'
            with open(file_path, 'w') as f:
                json.dump(result, f)
            print(f"Debug: Full response saved to {file_path}")
            return result_str[:20000]
        else:
            return result_str