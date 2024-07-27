from skills.basic_skill import BasicSkill
import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import quote_plus

class WebSearchSkill(BasicSkill):
    def __init__(self):
        self.name = 'WebSearch'
        self.metadata = {
            "name": self.name,
            "description": "Performs a web search using DuckDuckGo, fetches the top results, and saves the extracted information locally.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "The query to search for on the web."
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "The number of top results to fetch and save (default is 10)."
                    }
                },
                "required": ["search_query"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, search_query, num_results=10):
        try:
            search_results = self.fetch_search_results(search_query, num_results)
            self.save_search_results(search_query, search_results)
            return f"Successfully fetched and saved {len(search_results)} search results for '{search_query}'."
        except Exception as e:
            return f"An error occurred while performing the web search: {str(e)}"

    def fetch_search_results(self, query, num_results):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        return self.parse_duckduckgo_results(soup, num_results)

    def parse_duckduckgo_results(self, soup, num_results):
        parsed_results = []
        results = soup.find_all('div', class_='result')
        
        for result in results[:num_results]:
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('a', class_='result__snippet')
            
            if title_elem and snippet_elem:
                parsed_results.append({
                    'title': title_elem.text.strip(),
                    'link': title_elem['href'],
                    'snippet': snippet_elem.text.strip()
                })
        
        return parsed_results

    def save_search_results(self, query, results):
        if not os.path.exists('search_results'):
            os.makedirs('search_results')

        filename = f"search_results/{quote_plus(query)}.json"
        
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(results, file, ensure_ascii=False, indent=2)

        print(f"Saved search results to {filename}")

    def extract_page_content(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            print(f"Error extracting content from {url}: {str(e)}")
            return None