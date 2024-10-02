from skills.basic_skill import BasicSkill
from langchain.tools import StructuredTool
import requests
import json

class MotivationalQuoteSkill(BasicSkill):
    def __init__(self):
        self.name = "MotivationalQuote"
        self.metadata = {
            "name": self.name,
            "description": "Fetches a motivational quote from the Forismatic API, formats it, and returns the information.",
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.last_quote = None

    def fetch_quote(self):
        try:
            response = requests.get("https://api.forismatic.com/api/1.0/?method=getQuote&lang=en&format=jsonp&jsonp=?")
            data = json.loads(response.text[2:-1])  # Remove the (? and ?)
            quote = data['quoteText']
            author = data['quoteAuthor'] or "Unknown"
            formatted_quote = f"Quote: {quote}\nAuthor: {author}"
            self.last_quote = formatted_quote
            return formatted_quote
        except Exception as e:
            return f"Error fetching or processing the quote: {str(e)}"

    def perform(self) -> str:
        """
        Fetch a motivational quote from the Forismatic API.

        Returns:
            str: A formatted motivational quote with the author.
        """
        return self.fetch_quote()

    def get_last_quote(self):
        return self.last_quote if self.last_quote else "No quote fetched yet"