from skills.basic_skill import BasicSkill
from langchain.tools import StructuredTool
import os
import requests

class WebSearchSkill(BasicSkill):
    def __init__(self):
        self.name = "WebSearch"
        self.metadata = {
            "name": self.name,
            "description": "Searches the web using the SerpApi and returns a summary of the results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to be sent to SerpApi"
                    }
                },
                "required": ["query"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.api_key = os.getenv('SERPAPI_API_KEY')

    def perform(self, query: str) -> str:
        """
        Perform a web search using the SerpApi.

        Args:
            query (str): The search query.

        Returns:
            str: A summary of the search results.
        """
        if not self.api_key:
            return "Error: SerpApi API key not found. Please set the SERPAPI_API_KEY environment variable."

        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.api_key,
                "engine": "google"
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "error" in data:
                return f"Error from SerpApi: {data['error']}"

            organic_results = data.get("organic_results", [])
            
            summary = f"Here are the top results for '{query}':\n\n"
            for i, result in enumerate(organic_results[:5], 1):
                title = result.get("title", "No title")
                snippet = result.get("snippet", "No snippet available")
                summary += f"{i}. {title}\n   {snippet}\n\n"

            return summary

        except requests.RequestException as e:
            return f"An error occurred while searching: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"