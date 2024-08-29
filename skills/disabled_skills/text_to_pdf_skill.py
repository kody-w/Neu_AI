from skills.basic_skill import BasicSkill
from fpdf import FPDF
class TextoPDFSkill(BasicSkill):
    def __init__(self):
        self.name = 'TexttoPDF'
        self.metadata = {
            "name": self.name,
            "description": "Converts a given story text into a formatted PDF suitable for ebook publishing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "story_text": {
                        "type": "string",
                        "description": "The full text of the story to be converted into an ebook format."
                    }
                },
                "required": ["story_text"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, story_text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        for line in story_text.split('\n'):
            pdf.cell(0, 10, line, ln=True)
        output_path = 'story_ebook.pdf'
        pdf.output(output_path, 'F')
        return 'Successfully converted the story to a PDF. The file is saved as ' + output_path
