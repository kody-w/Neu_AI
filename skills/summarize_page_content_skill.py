from skills.basic_skill import BasicSkill
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import Counter
import os
import json
from datetime import datetime

class SummarizePageContentSkill(BasicSkill):
    def __init__(self):
        self.name = "SummarizePageContent"
        self.metadata = {
            "name": self.name,
            "description": "Retrieves a webpage, saves it locally, then summarizes its content and suggests relevant links to explore next.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The webpage URL to analyze and summarize."
                    },
                    "num_summary_sentences": {
                        "type": "integer",
                        "description": "Number of sentences to include in the summary (default is 3)."
                    },
                    "num_suggested_links": {
                        "type": "integer",
                        "description": "Number of links to suggest (default is 5)."
                    }
                },
                "required": ["url"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        # Download NLTK data (if not already downloaded)
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)

        # Ensure the saved_content directory exists
        self.content_dir = os.path.join(os.getcwd(), 'saved_content')
        os.makedirs(self.content_dir, exist_ok=True)

    def perform(self, url, num_summary_sentences=3, num_suggested_links=5):
        try:
            # Fetch and save the webpage content
            html_file_path = self.fetch_and_save_content(url)

            # Load and parse the saved HTML content
            with open(html_file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract and clean text content
            text_content = self.extract_text_content(soup)

            # Generate summary
            summary = self.generate_summary(text_content, num_summary_sentences)

            # Extract and analyze links
            suggested_links = self.analyze_and_suggest_links(soup, url, num_suggested_links)

            # Prepare the output
            output = f"Summary of {url}:\n\n{summary}\n\nSuggested links to explore:\n"
            for link in suggested_links:
                output += f"- {link['text']}: {link['url']} (Relevance: {link['relevance_score']})\n"

            output += f"\nLocal HTML file saved at: {html_file_path}"

            return output

        except Exception as e:
            return f"Failed to analyze webpage content. Error: {str(e)}"

    def fetch_and_save_content(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Generate a filename based on the URL and timestamp
        parsed_url = urlparse(url)
        base_filename = self.sanitize_filename(parsed_url.netloc + parsed_url.path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_filename}_{timestamp}.html"
        filepath = os.path.join(self.content_dir, filename)

        # Save the content
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(response.text)

        return filepath

    def sanitize_filename(self, filename):
        # Remove invalid characters and limit length
        return "".join(x for x in filename if x.isalnum() or x in "._- ")[:255]

    def extract_text_content(self, soup):
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

    def generate_summary(self, text, num_sentences):
        # Tokenize the text into sentences
        sentences = sent_tokenize(text)

        # Tokenize the text into words
        words = word_tokenize(text.lower())

        # Remove stopwords and non-alphabetic tokens
        stop_words = set(stopwords.words('english'))
        words = [word for word in words if word.isalnum() and word not in stop_words]

        # Calculate word frequencies
        word_freq = Counter(words)

        # Calculate sentence scores based on word frequencies
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            for word in word_tokenize(sentence.lower()):
                if word in word_freq:
                    if i not in sentence_scores:
                        sentence_scores[i] = word_freq[word]
                    else:
                        sentence_scores[i] += word_freq[word]

        # Get the top N sentences with the highest scores
        summary_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
        summary = ' '.join([sentences[i] for i in sorted(summary_sentences)])

        return summary

    def analyze_and_suggest_links(self, soup, base_url, num_links):
        links = soup.find_all('a', href=True)
        link_data = []

        for link in links:
            href = link['href']
            text = link.text.strip()

            # Resolve relative URLs
            full_url = urljoin(base_url, href)

            # Only consider links to the same domain
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                link_data.append({
                    'url': full_url,
                    'text': text,
                    'relevance_score': self.calculate_link_relevance(text, soup)
                })

        # Sort links by relevance score and return top N
        suggested_links = sorted(link_data, key=lambda x: x['relevance_score'], reverse=True)[:num_links]
        return suggested_links

    def calculate_link_relevance(self, link_text, soup):
        # This is a simple relevance calculation. You can make this more sophisticated.
        page_text = soup.get_text().lower()
        link_words = link_text.lower().split()
        
        # Remove stopwords from link text
        stop_words = set(stopwords.words('english'))
        link_words = [word for word in link_words if word not in stop_words]

        # Calculate relevance based on frequency of link words in page text
        relevance = sum(page_text.count(word) for word in link_words)

        return relevance