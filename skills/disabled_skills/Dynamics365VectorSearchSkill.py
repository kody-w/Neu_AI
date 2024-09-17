import json
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from skills.basic_skill import BasicSkill
import logging

class Dynamics365VectorSearchSkill(BasicSkill):
    def __init__(self, db_path='dynamics365_vector_db.json', response_data_file='response_data.json'):
        super().__init__(name='Dynamics365VectorSearch', metadata={})
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.name = 'Dynamics365VectorSearch'
        self.metadata = {
            "name": self.name,
            "description": "Performs vector searches on Dynamics 365 data based on input parameters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "refresh"],
                        "description": "The action to perform: 'search' to query the database, 'refresh' to reload data from response_data.json."
                    },
                    "query": {
                        "type": "string",
                        "description": "The search query for the 'search' action."
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "The number of top results to return for the 'search' action. Default is 5."
                    }
                },
                "required": ["action"]
            }
        }

        self.db_path = db_path
        self.response_data_file = response_data_file
        self.vectorizer = TfidfVectorizer()
        self.db = self.load_or_create_db()

    def load_or_create_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                self.logger.info("Loading existing database.")
                db = json.load(f)
                if db['entries']:
                    self.vectorizer.fit([entry['text'] for entry in db['entries']])
                return db
        else:
            self.logger.info("Creating new database.")
            return self.load_from_response_data()

    def load_from_response_data(self):
        if not os.path.exists(self.response_data_file):
            self.logger.warning(f"Response data file {self.response_data_file} not found. Creating empty database.")
            return {'entries': []}

        with open(self.response_data_file, 'r') as f:
            response_data = json.load(f)

        entries = []
        for item in response_data.get('value', []):
            text = self.create_searchable_text(item)
            entries.append({
                'text': text,
                'metadata': item
            })

        self.vectorizer.fit([entry['text'] for entry in entries])
        db = {'entries': entries}
        self.save_db(db)
        self.logger.info(f"Loaded {len(entries)} entries from response data.")
        return db

    def create_searchable_text(self, item):
        text_parts = []
        for key, value in item.items():
            if isinstance(value, (str, int, float)) and not key.startswith('_'):
                text_parts.append(f"{key}: {value}")
        return " | ".join(text_parts)

    def save_db(self, db):
        with open(self.db_path, 'w') as f:
            json.dump(db, f)

    def perform(self, action, query=None, top_k=5):
        try:
            if action == "search":
                results = self.search_db(query, top_k)
                return self.format_results_as_text(results, query)
            elif action == "refresh":
                self.db = self.load_from_response_data()
                return f"Refreshed database with {len(self.db['entries'])} entries."
            else:
                return "Invalid action. Please use 'search' or 'refresh'."
        except Exception as e:
            self.logger.error(f"Error in perform method: {str(e)}")
            return f"An error occurred: {str(e)}"

    def search_db(self, query, top_k=5):
        if not self.db['entries']:
            return "The database is empty. No data available for search."

        query_vector = self.vectorizer.transform([query])
        all_vectors = self.vectorizer.transform([entry['text'] for entry in self.db['entries']])
        
        similarities = cosine_similarity(query_vector, all_vectors)[0]
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "score": float(similarities[idx]),
                "data": self.db['entries'][idx]['metadata']
            })

        return results

    def format_results_as_text(self, results, query):
        if isinstance(results, str):
            return results

        formatted_results = [f"Search results for '{query}':\n"]
        for i, result in enumerate(results, 1):
            formatted_result = [f"Result {i} (Relevance Score: {result['score']:.2f}):"]
            for key, value in result['data'].items():
                if not key.startswith('_') and value is not None:
                    formatted_result.append(f"{key}: {value}")
            formatted_results.append("\n".join(formatted_result))

        return "\n\n".join(formatted_results)

# Example usage:
# dynamics365_search = Dynamics365VectorSearchSkill()
# print(dynamics365_search.perform(action="search", query="Windows XP", top_k=3))
# print(dynamics365_search.perform(action="refresh"))