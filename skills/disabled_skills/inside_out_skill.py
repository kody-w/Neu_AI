import json
import numpy as np
from scipy.sparse import issparse, csr_matrix
from scipy.spatial.distance import cosine
from sklearn.feature_extraction.text import TfidfVectorizer
from skills.basic_skill import BasicSkill
import logging
from datetime import datetime, timedelta
import hashlib
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoreMemory:
    def __init__(self, id, content, emotion, importance, timestamp):
        self.id = id
        self.content = content
        self.emotion = emotion
        self.importance = importance
        self.timestamp = datetime.fromisoformat(timestamp)
        self.associated_memories = []

class AssociatedMemory:
    def __init__(self, id, content, core_memory_id, timestamp):
        self.id = id
        self.content = content
        self.core_memory_id = core_memory_id
        self.timestamp = datetime.fromisoformat(timestamp)

class CoreMemoryHopfieldSearchSkill(BasicSkill):
    def __init__(self):
        self.name = 'CoreMemoryHopfieldSearch'
        self.metadata = {
            "name": self.name,
            "description": "Advanced search using a core memory architecture with Hopfield network-based approach.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The main search query to find relevant memories."
                    },
                    "emotion": {
                        "type": "string",
                        "description": "The emotional context of the query."
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time range for memory search (e.g., 'recent', 'past_week', 'all')"
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
                "required": ["query", "emotion", "time_range", "top_k", "threshold"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.memory_file = 'core_memories.json'
        self.core_memories = []
        self.associated_memories = []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self._load_memories()
        self.memory_vectors = self._vectorize_memories()
        
        # New attributes for caching
        self.cache_dir = 'search_cache'
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _load_memories(self):
        try:
            with open(self.memory_file, 'r') as file:
                data = json.load(file)
                for core_mem in data['core_memories']:
                    cm = CoreMemory(core_mem['id'], core_mem['content'], core_mem['emotion'], 
                                    core_mem['importance'], core_mem['timestamp'])
                    self.core_memories.append(cm)
                for assoc_mem in data['associated_memories']:
                    am = AssociatedMemory(assoc_mem['id'], assoc_mem['content'], 
                                          assoc_mem['core_memory_id'], assoc_mem['timestamp'])
                    self.associated_memories.append(am)
                    core_mem = next(cm for cm in self.core_memories if cm.id == am.core_memory_id)
                    core_mem.associated_memories.append(am)
            logger.debug(f"Loaded {len(self.core_memories)} core memories and {len(self.associated_memories)} associated memories")
        except FileNotFoundError:
            logger.warning(f"Memory file {self.memory_file} not found. Initializing with empty memories.")
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {self.memory_file}")

    def _vectorize_memories(self):
        all_memories = [cm.content for cm in self.core_memories] + [am.content for am in self.associated_memories]
        if not all_memories:
            logger.warning("No memories to vectorize")
            return csr_matrix((0, 0))
        vectors = self.vectorizer.fit_transform(all_memories)
        logger.debug(f"Vectorized {len(all_memories)} memories. Shape: {vectors.shape}")
        return vectors

    def _to_dense(self, x):
        return x.toarray() if issparse(x) else np.array(x)

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
        return similarity

    def _get_time_range_filter(self, time_range):
        now = datetime.now()
        if time_range == 'recent':
            return now - timedelta(days=1)
        elif time_range == 'past_week':
            return now - timedelta(weeks=1)
        else:  # 'all'
            return datetime.min

    def _generate_cache_key(self, query, emotion, time_range, top_k, threshold):
        # Generate a unique key for the search parameters
        params = f"{query}|{emotion}|{time_range}|{top_k}|{threshold}"
        return hashlib.md5(params.encode()).hexdigest()

    def _save_to_cache(self, cache_key, results):
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f, indent=2)
        logger.info(f"Search results cached to {cache_file}")

    def _get_from_cache(self, cache_key, max_age_hours=24):
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < timedelta(hours=max_age_hours):
                logger.info(f"Retrieved results from cache: {cache_file}")
                return cached_data['results']
        return None

    def perform(self, query, emotion, time_range, top_k, threshold):
        cache_key = self._generate_cache_key(query, emotion, time_range, top_k, threshold)
        cached_results = self._get_from_cache(cache_key)
        if cached_results:
            logger.info("Returning cached results")
            return json.dumps(cached_results, indent=2)

        logger.info(f"Performing search with query: '{query}', emotion: {emotion}, time_range: {time_range}, top_k: {top_k}, threshold: {threshold}")
        if not self.core_memories and not self.associated_memories:
            logger.warning("No memories found in the database.")
            return json.dumps({"error": "No memories found in the database."})

        query_vector = self.vectorizer.transform([query])
        logger.debug(f"Query vector shape: {query_vector.shape}")

        updated_query = self._hopfield_update(query_vector)
        logger.debug(f"Updated query shape: {updated_query.shape}")

        time_filter = self._get_time_range_filter(time_range)
        similarities = []
        for i, memory_vector in enumerate(self.memory_vectors):
            if i < len(self.core_memories):
                memory = self.core_memories[i]
                if memory.timestamp < time_filter:
                    continue
                similarity = self._calculate_similarity(updated_query, memory_vector)
                emotion_boost = 0.1 if memory.emotion.lower() == emotion.lower() else 0
                recency_boost = (datetime.now() - memory.timestamp).days / 365.0  # Boost for more recent memories
                importance_boost = memory.importance * 0.1
                adjusted_similarity = similarity + emotion_boost + recency_boost + importance_boost
            else:
                memory = self.associated_memories[i - len(self.core_memories)]
                if memory.timestamp < time_filter:
                    continue
                similarity = self._calculate_similarity(updated_query, memory_vector)
                adjusted_similarity = similarity
            
            logger.debug(f"Memory {i}: Base similarity: {similarity}, Adjusted: {adjusted_similarity}")
            if adjusted_similarity >= threshold:
                similarities.append((i, adjusted_similarity))

        top_results = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
        logger.debug(f"Top results: {top_results}")

        results = []
        for index, similarity in top_results:
            if index < len(self.core_memories):
                memory = self.core_memories[index]
                mem_type = "core"
            else:
                memory = self.associated_memories[index - len(self.core_memories)]
                mem_type = "associated"
            
            results.append({
                'id': memory.id,
                'content': memory.content,
                'type': mem_type,
                'emotion': memory.emotion if mem_type == "core" else None,
                'importance': memory.importance if mem_type == "core" else None,
                'timestamp': memory.timestamp.isoformat(),
                'similarity': float(similarity)
            })

        logger.info(f"Returning {len(results)} results")
        self._save_to_cache(cache_key, results)
        return json.dumps(results, indent=2)

    def add_core_memory(self, content, emotion, importance):
        logger.info(f"Adding new core memory: {content}")
        new_id = max([cm.id for cm in self.core_memories], default=0) + 1
        new_core_memory = CoreMemory(new_id, content, emotion, importance, datetime.now().isoformat())
        self.core_memories.append(new_core_memory)
        self._update_memory_vectors()
        self._save_memories()

    def add_associated_memory(self, content, core_memory_id):
        logger.info(f"Adding new associated memory: {content}")
        new_id = max([am.id for am in self.associated_memories], default=0) + 1
        new_associated_memory = AssociatedMemory(new_id, content, core_memory_id, datetime.now().isoformat())
        self.associated_memories.append(new_associated_memory)
        core_memory = next(cm for cm in self.core_memories if cm.id == core_memory_id)
        core_memory.associated_memories.append(new_associated_memory)
        self._update_memory_vectors()
        self._save_memories()

    def _update_memory_vectors(self):
        self.memory_vectors = self._vectorize_memories()

    def _save_memories(self):
        data = {
            'core_memories': [{'id': cm.id, 'content': cm.content, 'emotion': cm.emotion, 
                               'importance': cm.importance, 'timestamp': cm.timestamp.isoformat()} 
                              for cm in self.core_memories],
            'associated_memories': [{'id': am.id, 'content': am.content, 'core_memory_id': am.core_memory_id, 
                                     'timestamp': am.timestamp.isoformat()} 
                                    for am in self.associated_memories]
        }
        with open(self.memory_file, 'w') as file:
            json.dump(data, file, indent=2)
        logger.debug(f"Saved {len(self.core_memories)} core memories and {len(self.associated_memories)} associated memories")

# Example usage (commented out)
'''
if __name__ == "__main__":
    skill = CoreMemoryHopfieldSearchSkill()
    
    # Example: Search for memories related to a family outing
    results = skill.perform(
        query="family outing",
        emotion="happy",
        time_range="all",
        top_k=5,
        threshold=0.1
    )
    
    print("Search Results:", results)

    # Example: Add a new core memory
    skill.add_core_memory("Enjoyed a wonderful picnic in the park with family", "joyful", 0.8)

    # Example: Add an associated memory
    skill.add_associated_memory("Saw beautiful butterflies during the picnic", 1)  # Assuming 1 is the ID of the core memory

    print("Memory added successfully")

    # Example: Perform the same search again to demonstrate caching
    cached_results = skill.perform(
        query="family outing",
        emotion="happy",
        time_range="all",
        top_k=5,
        threshold=0.1
    )
    
    print("Cached Search Results:", cached_results)
'''