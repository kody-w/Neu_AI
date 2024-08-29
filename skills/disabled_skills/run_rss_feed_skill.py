from skills.basic_skill import BasicSkill
import feedparser
import ssl
from datetime import datetime

class RSSFeedReaderSkill(BasicSkill):
    def __init__(self):
        self.name = "RSSFeedReader"
        self.metadata = {
            "name": self.name,
            "description": "Fetches and returns the latest entries from an RSS feed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "feed_url": {
                        "type": "string",
                        "description": "URL of the RSS feed to read."
                    },
                    "num_entries": {
                        "type": "integer",
                        "description": "Number of entries to return (default is 5)."
                    }
                },
                "required": ["feed_url"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, feed_url, num_entries=5):
        try:
            # Disable SSL certificate verification (use with caution)
            if hasattr(ssl, '_create_unverified_context'):
                ssl._create_default_https_context = ssl._create_unverified_context

            # Parse the feed
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                return f"Error parsing the feed: {feed.bozo_exception}"

            # Extract and format the latest entries
            entries = []
            for entry in feed.entries[:num_entries]:
                published = entry.get('published', 'No date')
                try:
                    published = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass  # Keep the original string if parsing fails

                entries.append({
                    'title': entry.get('title', 'No title'),
                    'link': entry.get('link', 'No link'),
                    'published': published,
                    'summary': entry.get('summary', 'No summary')[:200] + '...' if entry.get('summary') else 'No summary'
                })

            # Prepare the response
            response = f"Latest {num_entries} entries from {feed.feed.title}:\n\n"
            for i, entry in enumerate(entries, 1):
                response += f"{i}. {entry['title']}\n"
                response += f"   Published: {entry['published']}\n"
                response += f"   Link: {entry['link']}\n"
                response += f"   Summary: {entry['summary']}\n\n"

            return response

        except Exception as e:
            return f"Error fetching the RSS feed: {str(e)}"