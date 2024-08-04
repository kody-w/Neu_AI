from skills.basic_skill import BasicSkill
import requests
from bs4 import BeautifulSoup

class WebSearchSkill(BasicSkill):
    def __init__(self):
        self.name = "WebSearch"
        self.metadata = {
            "name": self.name,
            "description": "Performs web scraping and internet searches.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or URL to scrape."
                    },
                    "action": {
                        "type": "string",
                        "enum": ["search", "scrape"],
                        "description": "The action to perform (search or scrape)."
                    }
                },
                "required": ["query", "action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, query, action):
        if action == "search":
            return self.search(query)
        elif action == "scrape":
            return self.scrape(query)
        else:
            return "Invalid action for WebSearchSkill."

    def search(self, query):
        try:
            url = f"https://www.google.com/search?q={query}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for g in soup.find_all('div', class_='g'):
                anchor = g.find('a')
                if anchor:
                    link = anchor['href']
                    title = g.find('h3', class_='r')
                    if title:
                        results.append(f"{title.text} - {link}")
            return "\n".join(results[:5])  # Return top 5 results
        except Exception as e:
            return f"Error performing web search: {str(e)}" 

    def scrape(self, url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text()[:500]  # Return first 500 characters of scraped content
        except Exception as e:
            return f"Error scraping webpage: {str(e)}"