from skills.basic_skill import BasicSkill

class FetchXMLTranslatorSkill(BasicSkill):
    def __init__(self):
        self.name = "FetchXMLTranslator"
        self.metadata = {
            "name": self.name,
            "description": "This skill translates user requests into valid FetchXML queries for Dynamics API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fetchXML": {
                        "type": "string",
                        "description": "The user request translated into FetchXML."
                    }
                },
                "required": ["fetchXML"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, fetchXML):
        # Translate user request into valid FetchXML query
        # Implement the translation logic here
        fetchxml_query = "<fetch version=\"1.0\" output-format=\"xml-platform\" mapping=\"logical\" distinct=\"false\">"
        fetchxml_query += fetchXML
        fetchxml_query += "</fetch>"
        return fetchxml_query