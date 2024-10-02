import base64
from skills.basic_skill import BasicSkill
import os
class SaveImageLocallySkill(BasicSkill):
    def __init__(self):
        self.name = "SaveImageLocally"
        self.metadata = {
            "name": self.name,
            "description": "Saves a base64 encoded image string to a local file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "base64_image": {
                        "type": "string",
                        "description": "The base64 encoded image string to be saved."
                    },
                    "file_path": {
                        "type": "string",
                        "description": "The file path where the image should be saved." 
                    }
                },
                "required": ["base64_image", "file_path"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, base64_image, file_path):
        image_data = base64.b64decode(base64_image.split(',')[1])
        with open(file_path, 'wb') as f:
            f.write(image_data)
        return f"Image saved to {file_path}."