from skills.basic_skill import BasicSkill
import json
from scrapegraphai.graphs import SmartScraperGraph
import os
from openai import AzureOpenAI

class SmartScraperSkill(BasicSkill):
    def __init__(self):
        self.name = "SmartScraper"
        self.metadata = {
            "name": self.name,
            "description": "Performs intelligent web scraping using SmartScraperGraph to extract specific information from a given URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt describing what information to extract from the website."
                    },
                    "url": {
                        "type": "string",
                        "description": "The URL of the website to scrape."
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Whether to enable verbose output (default: True).",
                        "default": True
                    },
                    "headless": {
                        "type": "boolean",
                        "description": "Whether to run the browser in headless mode (default: False).",
                        "default": False
                    }
                },
                "required": ["prompt", "url"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.load_api_config()

    def load_api_config(self):
        config_path = 'config/api_keys.json'
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"API configuration file not found at {config_path}")
        
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        
        self.api_key = config.get('azure_openai_api_key')
        self.api_base = config.get('azure_openai_endpoint')
        self.api_version = config.get('azure_openai_api_version')
        
        if not all([self.api_key, self.api_base, self.api_version]):
            raise ValueError("Missing required API configuration in api_keys.json")

    def perform(self, prompt, url, verbose=True, headless=False):
        try:
            # Create AzureOpenAI client
            client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.api_base
            )

            # Define the configuration for the scraping pipeline
            graph_config = {
                "llm": {
                    "type": "azure",
                    "client": client,
                    "model": "gpt-4o",  # Add this line back
                    "deployment": "gpt-4o",
                    "api_key": self.api_key,
                    "api_base": self.api_base,
                    "api_version": self.api_version,
                },
                "verbose": verbose,
                "headless": headless,
            }

            # Create the SmartScraperGraph instance
            smart_scraper_graph = SmartScraperGraph(
                prompt=prompt,
                source=url,
                config=graph_config
            )

            # Run the pipeline
            result = smart_scraper_graph.run()

            # Return the result as a formatted JSON string
            return json.dumps(result, indent=4)
        except Exception as e:
            return f"An error occurred during web scraping: {str(e)}\nFull error details: {type(e).__name__}: {str(e)}"