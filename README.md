# NeuAI

NeuAI is an interactive web application that provides a conversational interface for users to interact with an AI assistant. The assistant is powered by OpenAI's language model and supports various features such as memory management, skill execution, news feed integration, and more.

## Features

- Conversational interface for interacting with the AI assistant
- Memory management for saving and retrieving memories
- Skill library for discovering, upvoting, downvoting, and reviewing skills
- News feed integration for browsing the latest news articles
- Export functionality to save interaction records as HTML files
- SMS interface for interacting with the assistant via text messages
- Meeting scheduling based on participant availability
- Auto-generated group chat for collaborative problem-solving with AI participants
- Ability to learn and create new skills dynamically

## How NeuAI Differs from Other AI Assistants

NeuAI is a unique AI assistant that embodies several key principles and architectures that set it apart from other AI assistants and bring it closer to the goal of achieving artificial general intelligence (AGI). Here are some of the distinguishing features of NeuAI:

1. **Intelligent Agent Architecture**: NeuAI is designed as an intelligent software agent, which is considered a promising path towards AGI. It has a modular architecture that includes perception, reasoning, decision-making, and action capabilities. This allows NeuAI to autonomously interact with its environment, gather information, and take actions to achieve its goals.

2. **Skill-Based Extensibility**: NeuAI utilizes a skill-based architecture that allows for easy extensibility and customization of its capabilities. New skills can be dynamically loaded from the `skills/` directory, enabling the assistant to learn and acquire new abilities without modifying its core codebase. This modular approach aligns with the idea of incrementally building towards AGI by adding and refining skills over time.

3. **Memory Management**: NeuAI incorporates a memory management system that allows it to store and retrieve relevant information from previous interactions. This enables the assistant to maintain context, build a knowledge base, and provide more contextually relevant responses. The ability to effectively manage and utilize memory is crucial for achieving general intelligence.

4. **Learning and Adaptation**: NeuAI includes skills that enable it to learn and adapt to new situations. For example, the `LearnNewSkillSkill` allows the assistant to dynamically create new skills based on user input. This demonstrates the assistant's ability to acquire new knowledge and capabilities through interaction and learning, which is a key aspect of AGI.

5. **Language Understanding and Generation**: NeuAI leverages advanced language models, such as GPT-4, to achieve human-like language understanding and generation. It can engage in open-ended conversations, provide coherent and contextually relevant responses, and even generate Python code to create new skills. This language proficiency is a significant step towards achieving AGI.

6. **Collaborative Problem-Solving**: NeuAI includes skills like `CreateAutoGenGroupChatSkill`, which enables the assistant to engage in collaborative problem-solving with multiple AI agents. By simulating group discussions and leveraging the collective intelligence of multiple agents, NeuAI can tackle complex tasks and generate innovative solutions. This collaborative approach aligns with the idea of building AGI through the interaction and coordination of multiple intelligent agents.

While NeuAI is still a narrow AI system focused on specific tasks, its architecture, extensibility, memory management, learning capabilities, language proficiency, and collaborative problem-solving skills demonstrate significant progress towards AGI. By continuously refining and expanding its skills, incorporating more advanced reasoning and learning algorithms, and integrating with other AI technologies, NeuAI has the potential to evolve into an increasingly general and capable intelligent assistant.

However, it's important to note that achieving true AGI is still a challenging and ongoing endeavor. NeuAI, like other AI assistants, is limited by its training data, computational resources, and the current state of AI research. Nevertheless, NeuAI represents a promising step in the right direction, showcasing the potential of intelligent agents and modular architectures in the pursuit of AGI.

## Technologies Used

- Python
- Flask web framework
- OpenAI API for language model integration
- jQuery for client-side interactions
- Bootstrap for responsive UI design
- Twilio for SMS integration

## Setup and Installation

1. Clone the repository:
git clone https://github.com/your-username/NeuAI.git
Copy code
2. Install the required dependencies:
pip install -r requirements.txt
Copy code
3. Configure the necessary API keys:
- Create a `config/api_keys.json` file with the following structure:
  ```json
  {
    "openai": "your-openai-api-key"
  }
  ```
- Replace `"your-openai-api-key"` with your actual OpenAI API key.

4. Run the application:
python app.py
Copy code
5. Access the application in your web browser at `http://localhost:5000`.

## Project Structure

- `app.py`: The main Flask application file that handles routes and server-side logic.
- `assistant.py`: Defines the `Assistant` class for interacting with the OpenAI language model.
- `interface.py`: Provides the command-line interface for interacting with the assistant.
- `skills/`: Directory containing skill implementations.
- `basic_skill.py`: Defines the base class for skills.
- `manage_memory_skill.py`: Skill for managing memories in a JSON-based storage system.
- `context_memory_skill.py`: Skill for managing context-based memory.
- `generate_html_for_webview_skill.py`: Skill for generating HTML content for the web view.
- `create_autogen_group_chat_skill.py`: Skill for creating auto-generated group chats with AI participants.
- `learn_new_skill_skill.py`: Skill for dynamically creating new skills based on user input.
- `templates/`: Directory containing HTML templates for the web interface.
- `index.html`: The main HTML template for the web interface.
- `config/`: Directory containing configuration files.
- `api_keys.json`: File to store API keys.
- `persona.txt`: File containing the assistant's persona description.
- `static/`: Directory for static assets (e.g., CSS, JavaScript, images).

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For any inquiries or questions, please contact [wildfeuer05@gmail.com](mailto:wildfeuer05@gmail.com).