
# Llama_Agent

# LLamaAssistant

LLamaAssistant is an AI-powered personal assistant that uses the Groq API and LangChain framework to provide a versatile and interactive chat experience. It comes with various skills and can be extended with custom functionalities.

## Features

- Interactive chat interface (CLI and Streamlit)
- Utilizes Groq's language models
- Extensible skill system
- Built-in motivational quote generation
- Robust error handling and logging

## Prerequisites

- Python 3.9+
- Groq API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/LLamaAssistant.git
   cd LLamaAssistant
   ```
2. Create a virtual environment and activate it:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file from '.env copy' in the root directory and add your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
## Usage

### CLI Interface

Run the assistant in CLI mode:
```
python interface.py --cli
```
### Streamlit Interface

Run the assistant with a Streamlit web interface:
```
streamlit run interface.py
```
## Project Structure

- `interface.py`: Main entry point for the application
- `assistant.py`: Core assistant logic and API interactions
- `skills/`: Directory containing various skills
  - `basic_skill.py`: Base class for all skills
  - `motivational_quote_skill.py`: Skill for generating motivational quotes

## Adding New Skills

1. Create a new Python file in the `skills/` directory.
2. Define a new class that inherits from `BasicSkill`.
3. Implement the `perform` method with the desired functionality.
4. The skill will be automatically loaded when the assistant initializes.

Example:

```python
from skills.basic_skill import BasicSkill

class MyNewSkill(BasicSkill):
    def __init__(self):
        self.name = "MyNewSkill"
        self.metadata = {
            "name": self.name,
            "description": "Description of what my new skill does",
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self) -> str:
        # Implement your skill's functionality here
        return "Result of my new skill"
```
## Troubleshooting

If you encounter any issues:

- Check the console output for error messages.
- Ensure your Groq API key is correctly set in the .env file.
- Verify that all dependencies are installed correctly.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Test Case with Motivational Quote Skill

(base) ➜  Llama_Agent git:(main) ✗ python interface.py --cli
2024-07-31 17:08:08,028 - INFO - Loaded skills: MotivationalQuote
Welcome to the AI Assistant. Type 'exit' to end the conversation.
You: can you give me a motivational quote?
