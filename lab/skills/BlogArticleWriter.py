from skills.basic_skill import BasicSkill
import os
class BlogArticleWriterSkill(BasicSkill):
    def __init__(self):
        self.name = "BlogArticleWriter"
        self.metadata = {
            "name": self.name,
            "description": "Writes a blog article based on a provided topic and saves it in a .md format in a 'blog' directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the blog article."
                    },
                    "content": {
                        "type": "string",
                        "description": "The main content or body of the blog article. Should be in markdown format and be a substantial post for a technical blog."
                    }
                },
                "required": ["title", "content"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, title, content):
        try:
            # Ensure the 'blog' directory exists
            os.makedirs('blog', exist_ok=True)
            # Generate the file path
            file_path = os.path.join('blog', f"{title.replace(' ', '_').lower()}.md")
            # Write the content to the markdown file
            with open(file_path, 'w') as file:
                file.write(f"# {title}\n\n")
                file.write(content)
            return f"Article '{title}' successfully written to {file_path}"
        except Exception as e:
            return f"Failed to write article '{title}': {str(e)}"