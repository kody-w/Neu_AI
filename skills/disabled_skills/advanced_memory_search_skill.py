import json
import numpy as np
from scipy.sparse import issparse, csr_matrix
from scipy.spatial.distance import cosine
from sklearn.feature_extraction.text import TfidfVectorizer
from skills.basic_skill import BasicSkill
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedHopfieldMemorySearchSkill(BasicSkill):
    def __init__(self):
        self.name = 'AdvancedHopfieldMemorySearch'
        self.metadata = {
            "name": self.name,
            "description": "Advanced search for relevant memories using a Hopfield network-based approach with flexible association patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The main search query to find relevant memories."
                    },
                    "associations": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Additional terms or phrases to associate with the main query."
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of top results to return."
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Similarity threshold for including results (0.0 to 1.0)."
                    }
                },
                "required": ["query", "associations", "top_k", "threshold"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.memory_file = 'memory.json'
        self.memories = self._load_memories()
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.memory_vectors = self._vectorize_memories()
        logger.debug(f"Initialized with {len(self.memories)} memories")

    def _load_memories(self):
        try:
            with open(self.memory_file, 'r') as file:
                memories = json.load(file)
            logger.debug(f"Loaded {len(memories)} memories from {self.memory_file}")
            return memories
        except FileNotFoundError:
            logger.warning(f"Memory file {self.memory_file} not found. Initializing with empty memories.")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {self.memory_file}")
            return {}

    def _vectorize_memories(self):
        if not self.memories:
            logger.warning("No memories to vectorize")
            return csr_matrix((0, 0))
        memory_texts = [f"{mem['theme']} {mem['message']}" for mem in self.memories.values()]
        vectors = self.vectorizer.fit_transform(memory_texts)
        logger.debug(f"Vectorized {len(memory_texts)} memories. Shape: {vectors.shape}")
        return vectors

    def _to_dense(self, x):
        if issparse(x):
            return x.toarray()
        return np.array(x)

    def _hopfield_update(self, pattern, iterations=5):
        logger.debug(f"Performing Hopfield update. Input pattern shape: {pattern.shape}")
        if self.memory_vectors.shape[0] == 0:
            logger.warning("No memory vectors available for Hopfield update")
            return pattern
        weights = self._to_dense(self.memory_vectors.T.dot(self.memory_vectors))
        np.fill_diagonal(weights, 0)
        pattern = self._to_dense(pattern).flatten()
        for i in range(iterations):
            pattern = np.sign(weights.dot(pattern))
            logger.debug(f"Iteration {i+1}: Updated pattern shape: {pattern.shape}")
        return pattern.reshape(1, -1)

    def _calculate_similarity(self, query_vector, memory_vector):
        query_vector = self._to_dense(query_vector).flatten()
        memory_vector = self._to_dense(memory_vector).flatten()
        similarity = 1 - cosine(query_vector, memory_vector)
        logger.debug(f"Calculated similarity: {similarity}")
        return similarity

    def perform(self, query, associations, top_k, threshold):
        logger.info(f"Performing search with query: '{query}', associations: {associations}, top_k: {top_k}, threshold: {threshold}")
        if not self.memories:
            logger.warning("No memories found in the database.")
            return json.dumps({"error": "No memories found in the database."})

        combined_query = f"{query} {' '.join(associations)}"
        logger.debug(f"Combined query: '{combined_query}'")
        query_vector = self.vectorizer.transform([combined_query])
        logger.debug(f"Query vector shape: {query_vector.shape}")
        logger.debug(f"Memory vectors shape: {self.memory_vectors.shape}")

        if query_vector.shape[1] != self.memory_vectors.shape[1]:
            logger.warning("Vocabulary mismatch. Adjusting vectorizer...")
            self.vectorizer = TfidfVectorizer(stop_words='english', vocabulary=self.vectorizer.vocabulary_)
            query_vector = self.vectorizer.transform([combined_query])
            logger.debug(f"Adjusted query vector shape: {query_vector.shape}")

        updated_query = self._hopfield_update(query_vector)
        logger.debug(f"Updated query shape: {updated_query.shape}")

        similarities = []
        for memory_id, memory_vector in zip(self.memories.keys(), self.memory_vectors):
            similarity = self._calculate_similarity(updated_query, memory_vector)
            logger.debug(f"Similarity for memory {memory_id}: {similarity}")
            if similarity >= threshold:
                similarities.append((memory_id, similarity))

        top_results = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
        logger.debug(f"Top results: {top_results}")

        results = []
        for memory_id, similarity in top_results:
            memory = self.memories[memory_id]
            results.append({
                'id': memory_id,
                'message': memory['message'],
                'theme': memory['theme'],
                'date': memory['date'],
                'time': memory['time'],
                'similarity': float(similarity)
            })

        logger.info(f"Returning {len(results)} results")
        return json.dumps(results, indent=2)

    def add_memory(self, memory):
        logger.info(f"Adding new memory: {memory}")
        memory_id = str(len(self.memories) + 1)
        self.memories[memory_id] = memory
        
        new_text = f"{memory['theme']} {memory['message']}"
        self.vectorizer = TfidfVectorizer(stop_words='english', vocabulary=self.vectorizer.vocabulary_)
        new_vector = self.vectorizer.transform([new_text])
        
        if self.memory_vectors.shape[0] == 0:
            self.memory_vectors = new_vector
        else:
            self.memory_vectors = csr_matrix(np.vstack((self._to_dense(self.memory_vectors), self._to_dense(new_vector))))

        with open(self.memory_file, 'w') as file:
            json.dump(self.memories, file, indent=2)
        logger.debug(f"Updated memory vectors shape: {self.memory_vectors.shape}")

    def remove_memory(self, memory_id):
        logger.info(f"Removing memory with ID: {memory_id}")
        if memory_id in self.memories:
            del self.memories[memory_id]
            self.memory_vectors = self._vectorize_memories()
            with open(self.memory_file, 'w') as file:
                json.dump(self.memories, file, indent=2)
            logger.debug(f"Updated memory vectors shape: {self.memory_vectors.shape}")
        else:
            logger.warning(f"Memory with ID {memory_id} not found.")
            raise ValueError(f"Memory with ID {memory_id} not found.")

    def update_memory(self, memory_id, updated_memory):
        logger.info(f"Updating memory with ID: {memory_id}")
        if memory_id in self.memories:
            self.memories[memory_id] = updated_memory
            self.memory_vectors = self._vectorize_memories()
            with open(self.memory_file, 'w') as file:
                json.dump(self.memories, file, indent=2)
            logger.debug(f"Updated memory vectors shape: {self.memory_vectors.shape}")
        else:
            logger.warning(f"Memory with ID {memory_id} not found.")
            raise ValueError(f"Memory with ID {memory_id} not found.")

# Example usage:
# advanced_search = AdvancedHopfieldMemorySearchSkill()
# results = advanced_search.perform(
#     query="important business meeting",
#     associations=["client", "presentation", "contract"],
#     top_k=3,
#     threshold=0.5
# )
# print(results)