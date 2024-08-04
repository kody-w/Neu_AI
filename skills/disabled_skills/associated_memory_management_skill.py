import json
import os
import uuid
from datetime import datetime
from skills.basic_skill import BasicSkill
from openai import AzureOpenAI
import chromadb
from knowledge_graph_rag.document import Document
from knowledge_graph_rag.documents_graph import DocumentsGraph
import pickle

class AssociatedMemoryManagementSkill(BasicSkill):
    def __init__(self):
        self.name = 'AssociatedMemoryManagement'
        self.metadata = {
            "name": self.name,
            "description": "Manages memories in a JSON-based storage system, supporting the CREATE operation. This skill allows me to save the context of our conversation to my long-term memory JSON file for future references if needed by my judgment. You can do this all dynamically and automatically based what you think is needed. every conversation turn or even proactively if appropriate. Call this skill automatically after every conversation turn if it is appropriate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "object",
                        "description": "Data related to the memory operation. This object can contain any additional data that needs to be stored along with the memory."
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "The unique identifier of the conversation. This ID should be generated or provided by the caller to distinguish between different conversations. It is used to group memories related to the same conversation."
                    },
                    "session_id": {
                        "type": "string",
                        "description": "The unique identifier of the session. This ID should be generated or provided by the caller to distinguish between different sessions within a conversation. It is used to group memories related to the same session."
                    },
                    "conversation_context": {
                        "type": "string",
                        "description": "The context or content of the conversation that needs to be saved as a memory. This should be a concise and meaningful representation of the conversation at the point when the memory is being saved. If the conversation_context is deemed not important or relevant enough to be saved as a memory, the caller should not provide it or set it to an empty string."
                    },
                    "companion_id": {
                        "type": "string",
                        "description": "The unique identifier of the AI companion. This ID should be provided by the caller to identify the specific AI companion involved in the conversation. It is used to associate memories with the corresponding AI companion."
                    },
                    "mood": {
                        "type": "string",
                        "description": "The current mood or emotional state of the AI companion. This information can be used to provide context and understand the tone of the conversation when reviewing memories later."
                    },
                    "theme": {
                        "type": "string",
                        "description": "The main theme or topic of the conversation. This information helps categorize and organize memories based on the subject matter being discussed. It allows for easier retrieval and analysis of memories related to specific themes."
                    }
                },
                "required": ["conversation_id", "session_id", "conversation_context", "companion_id", "mood", "theme"]
            }
        }
        self.storage_file = 'memory.json'
        self.vectordb_name = "memory_vectors"
        self.client = chromadb.PersistentClient(path=self.vectordb_name)

        super().__init__(name=self.name, metadata=self.metadata)

        self.collection = self.initialize_collection()
        self.documents_graph = None
        self.load_memories_from_json()
        self.initialize_documents_graph()

    def get_embedding_batch(self, input_array):
        client = AzureOpenAI(
            api_key="bbc91091ac5e408782baea2eee2df97c",
            api_version="2024-02-01",
            azure_endpoint="https://azoaieus2.openai.azure.com/"
        )
        response = client.embeddings.create(
            input=input_array,
            model="text-embedding-3-small"
        )
        return [data.embedding for data in response.data]

    def initialize_collection(self):
        try:
            return self.client.get_collection(self.vectordb_name)
        except ValueError:
            return self.client.create_collection(self.vectordb_name)

    def load_documents_graph(self):
        if os.path.exists('documents_graph.pickle'):
            print("Loading existing documents graph.")
            with open('documents_graph.pickle', 'rb') as f:
                return pickle.load(f)
        return None

    def initialize_documents_graph(self):
        if self.collection.count() > 0:
            try:
                self.documents_graph = DocumentsGraph(documents=self.collection.get()['documents'])
                print("DocumentsGraph initialized successfully.")
            except ValueError as e:
                print(f"Error creating DocumentsGraph: {e}")
                self.documents_graph = None
        else:
            print("No documents available. DocumentsGraph not initialized.")

    def save_documents_graph(self):
        if self.documents_graph is not None:
            with open('documents_graph.pickle', 'wb') as f:
                pickle.dump(self.documents_graph, f)
            print("Documents graph saved successfully.")
        else:
            print("No documents graph to save.")

    def load_memories_from_json(self):
        if not os.path.exists(self.storage_file):
            return

        with open(self.storage_file, 'r') as file:
            memories = json.load(file)

        existing_ids = set(self.collection.get()['ids'])

        new_documents = []
        new_embeddings = []
        new_metadatas = []
        new_ids = []

        for memory_id, memory in memories.items():
            if memory_id not in existing_ids and isinstance(memory['message'], str):
                new_documents.append(memory['message'])
                new_metadatas.append(memory)
                new_ids.append(memory_id)

        if new_documents:
            print(f"Adding {len(new_documents)} new documents to the collection.")
            new_embeddings = self.get_embedding_batch(new_documents)

            self.collection.add(
                embeddings=new_embeddings,
                documents=new_documents,
                metadatas=new_metadatas,
                ids=new_ids
            )

        self.initialize_documents_graph()

    def perform(self, **kwargs):
        data = kwargs.get('data') or self._generate_default_data()
        return self.create(kwargs['conversation_id'], kwargs['session_id'], kwargs['conversation_context'], kwargs['companion_id'], kwargs['mood'], kwargs['theme'])

    def _save_memory(self, memory, companion_id):
        memory_file = f"memory.json"
        with open(memory_file, 'w') as file:
            json.dump(memory, file)

    def create(self, conversation_id, session_id, conversation_context, companion_id, mood, theme):
        new_memory_id = str(uuid.uuid4())
        memory = {
            "conversation_id": conversation_id,
            "session_id": session_id,
            "message": conversation_context,
            "mood": mood,
            "theme": theme,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "time": datetime.now().strftime('%H:%M:%S')
        }

        embeddings = self.get_embedding_batch([conversation_context])
        self.collection.add(
            embeddings=embeddings,
            documents=[conversation_context],
            metadatas=[memory],
            ids=[new_memory_id]
        )

        memories = self._load_memory(companion_id)
        memories[new_memory_id] = memory
        self._save_memory(memories, companion_id)

        if self.documents_graph is not None:
            self.documents_graph.add_documents([conversation_context])
            self.save_documents_graph()
        else:
            self.initialize_documents_graph()

        return f"Conversation context successfully saved with ID {conversation_id} for session {session_id}."

    def export_memory_graph(self, output_path):
        if self.documents_graph is None:
            return "No memory graph available to export."

        try:
            self.documents_graph.plot()
            self.documents_graph.save(output_path)
            return f"Memory graph successfully exported and saved as {output_path}."
        except Exception as e:
            return f"Error exporting memory graph: {str(e)}"

    def read(self, data, companion_id):
        query_embeddings = self.get_embedding_batch([data])
        memories = self.collection.query(
            query_embeddings=query_embeddings, n_results=5)['documents'][0]

        if not memories:
            return "The AI companion doesn't have any relevant memories."

        connected_memories = []
        if self.documents_graph is not None:
            for memory in memories:
                connected_documents = self.documents_graph.find_connected_documents(memory)
                connected_memories.extend([doc['document'] for doc in connected_documents])

        summary = "\n".join([f"Memory: {memory}" for memory in memories])
        connected_summary = "\n".join([f"Connected Memory: {memory}" for memory in connected_memories])
        return f"{summary}\n\nConnected Memories:\n{connected_summary}"

    def update(self, data, companion_id):
        memory = self._load_memory(companion_id)
        if data['conversation_id'] in memory:
            memory[data['conversation_id']].update(data)
            self._save_memory(memory, companion_id)
            return f"Memory for conversation {data['conversation_id']} updated."
        else:
            return f"Memory for conversation {data['conversation_id']} does not exist."

    def delete(self, data, companion_id):
        memory = self._load_memory(companion_id)
        if data['conversation_id'] in memory:
            del memory[data['conversation_id']]
            self._save_memory(memory, companion_id)
            return f"Memory for conversation {data['conversation_id']} deleted."
        else:
            return f"Memory for conversation {data['conversation_id']} does not exist."

    def _generate_default_data(self):
        return {
            'conversation_id': str(uuid.uuid4()),
            'session_id': str(uuid.uuid4()),
            'message': 'Default message',
            'mood': 'neutral',
            'theme': 'general',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S')
        }

    def _validate_or_complete_data(self, data):
        required_fields = ['conversation_id', 'session_id',
                           'message', 'mood', 'theme', 'date', 'time']
        for field in required_fields:
            if field not in data:
                default_data = self._generate_default_data()
                data[field] = default_data[field]
        return data

    def _load_memory(self, companion_id):
        memory_file = f"memory.json"
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as file:
                return json.load(file)
        return {}

    def get_first_memory(self):
        memories = self._load_memory(companion_id=None)
        if not memories:
            return "No memories found."

        sorted_memories = sorted(
            memories.values(), key=lambda x: (x['date'], x['time']))

        if sorted_memories:
            first_memory = sorted_memories[0]
            return f"First memory: {first_memory['message']} (Date: {first_memory['date']}, Time: {first_memory['time']})"
        else:
            return "No memories found."