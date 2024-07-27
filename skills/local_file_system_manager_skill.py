import os
import shutil
from skills.basic_skill import BasicSkill

class LocalFileSystemManagerSkill(BasicSkill):
    def __init__(self):
        self.name = "LocalFileSystemManager"
        self.metadata = {
            "name": self.name,
            "description": "Manage local file system directories and files through CRUD operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The CRUD operation to perform."
                    },
                    "path": {
                        "type": "string",
                        "description": "The file system path for the operation."
                    },
                    "data": {
                        "type": "string",
                        "description": "Data for operations like create and update."
                    }
                },
                "required": ["operation", "path"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, operation, path, data=None):
        if operation == "create":
            return self.create(path, data)
        elif operation == "read":
            return self.read(path)
        elif operation == "update":
            return self.update(path, data)
        elif operation == "delete":
            return self.delete(path)
        else:
            return "Invalid operation requested."

    def create(self, path, data):
        if os.path.isdir(path) or os.path.isfile(path):
            return "Path already exists."
        elif data:  # Assume it's a file creation request.
            with open(path, 'w') as file:
                file.write(data)
            return "File created."
        else:  # Directory creation if no data is provided.
            os.makedirs(path)
            return "Directory created."

    def read(self, path):
        if os.path.isdir(path):
            return ", ".join(os.listdir(path))
        elif os.path.isfile(path):
            with open(path, 'r') as file:
                return "Contents of file: " + file.read()
        else:
            return "Path does not exist."

    def update(self, path, data):
        if os.path.isfile(path):
            with open(path, 'w') as file:
                file.write(data)
            return "File updated."
        else:
            return "File does not exist."

    def delete(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path)
            return "Directory deleted."
        elif os.path.isfile(path):
            os.remove(path)
            return "File deleted."
        else:
            return "Path does not exist."