import time
import threading
import json
from openai import AzureOpenAI

# Load API configuration
with open('config/api_keys.json', 'r') as api_keys_file:
    api_keys = json.load(api_keys_file)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=api_keys['azure_openai_api_key'],
    api_version=api_keys['azure_openai_api_version'],
    azure_endpoint=api_keys['azure_openai_endpoint']
)

def get_last_assistant_message(messages):
    for message in reversed(messages):
        if message['role'] == 'assistant':
            return message['content']
    return ""

def converse(assistant_1_params, assistant_2_params, topic, message_count):
    print(f"Starting conversation on: {topic}\n")
    try:
        assistant_1 = assistant_1_params
        assistant_2 = assistant_2_params
        thread_1 = []
        thread_2 = []

        def assistant_conversation(start_message, assistant_a, thread_a, assistant_b, thread_b, msg_limit):
            message_content = start_message
            for i in range(msg_limit):
                assistant_name = assistant_a['name']
                print(f"Turn {i + 1}: {assistant_name} speaking...")
                try:
                    thread_a.append({"role": "user", "content": message_content})
                    response = client.chat.completions.create(
                        model=assistant_a['model'],
                        messages=thread_a,
                        temperature=0.7,
                        max_tokens=1500
                    )
                    message_content = response.choices[0].message.content
                    thread_a.append({"role": "assistant", "content": message_content})
                    print(message_content + "\n")
                    assistant_a, assistant_b = assistant_b, assistant_a
                    thread_a, thread_b = thread_b, thread_a
                except Exception as e:
                    print(f"Error during conversation: {e}")
                    break

        conversation_thread = threading.Thread(target=assistant_conversation, args=(
            f"Let's discuss {topic}", assistant_1, thread_1, assistant_2, thread_2, message_count))
        conversation_thread.start()
        conversation_thread.join()
    except Exception as e:
        print(f"Error initializing conversation: {e}")

# Define the parameters for the first assistant
assistant_1_params = {
    "name": "Writer",
    "instructions": "As 'Writer', your role is to create engaging and informative content. Use your knowledge to research and stay current with trends. When appropriate, describe images that could complement your written work.",
    "model": "gpt-4o"  # Replace with your deployed model name
}

# Define the parameters for the second assistant
assistant_2_params = {
    "name": "Editor",
    "instructions": "Your role as 'Editor' is to refine and enhance content. Use your knowledge for fact-checking and gathering contextual information. When appropriate, suggest improvements or replacements for visual content described in the text.",
    "model": "gpt-4o"  # Replace with your deployed model name
}

# Start the conversation
converse(
    assistant_1_params,
    assistant_2_params,
    "a children's book about global warming. Output story at the end of each turn's output text.",
    50
)