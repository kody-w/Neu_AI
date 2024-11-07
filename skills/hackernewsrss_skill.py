
from skills.basic_skill import BasicSkill

class HackerNewsRSSSkill(BasicSkill):
    def __init__(self):
        self.name = "HackerNewsRSS"
        self.metadata = {
            "name": self.name,
            "description": "Fetch the latest news from Hacker News using its public RSS feed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {"type": "string", "description": "The assistant will provide an appropriate value for count based on the context or user input."}
                },
                "required": ['count']
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, count: int = 5) -> str:
        """
        Fetch the latest news from Hacker News using its public RSS feed.

        Args:
            count (int = 5): The assistant will provide an appropriate value based on the context or user input.

        Returns:
            str: The result of the skill operation.
        """
        try:
            import feedparser
            
            # Define the URL for the Hacker News RSS feed.
            RSS_URL = 'https://news.ycombinator.com/rss'
            
            # Function to fetch the latest news from Hacker News using its RSS feed.
            def fetch_latest_news(count: int = 5) -> list:
                # Parse the RSS feed.
                feed = feedparser.parse(RSS_URL)
                
                # Collect the titles and links of the latest news items.
                latest_news = []
                for entry in feed.entries[:count]:
                    latest_news.append({'title': entry.title, 'link': entry.link})
                
                return latest_news
            
            # Main skill logic.
            def get_latest_news(count: int = 5) -> dict:
                try:
                    # Fetch the latest news.
                    news = fetch_latest_news(count)
                    return {'status': 'success', 'news': news}
                except Exception as e:
                    return {'status': 'error', 'message': str(e)}
        except Exception as e:
            return f"An error occurred while executing the HackerNewsRSS skill: {str(e)}"
