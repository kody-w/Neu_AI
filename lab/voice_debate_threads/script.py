import threading
from queue import Queue
from openai import AzureOpenAI
from gtts import gTTS
import pygame
import io
import tempfile
import os
import json

# Initialize pygame mixer
pygame.mixer.init()

# List to store conversation history
conversation_history = []

# Common topic for discussion
with open("topic1.txt", "r") as file:
    common_topic = file.read().strip()

# Queues for storing AI responses and their audio
ai_queue_1 = Queue()
ai_queue_2 = Queue()

# Load API configuration
with open('config/api_keys.json', 'r') as api_keys_file:
    api_keys = json.load(api_keys_file)

# Set up Azure OpenAI client
client = AzureOpenAI(
    api_key=api_keys['azure_openai_api_key'],
    api_version=api_keys['azure_openai_api_version'],
    azure_endpoint=api_keys['azure_openai_endpoint']
)

def query_azure_openai(prompt, history, ai_name):
    try:
        messages = [
            {"role": "system", "content": f"""You are a hardcore Tech Nerd Anti-AI named {ai_name} discussing {common_topic}.
            Respond with super high engagement in the format like a normal human discussion, like 'I think', 'well that is' etc.
            Engage in a thoughtful intellectual conversation about this topic and give your opinions.
            Keep your responses very short and conversational like a human talking to a human would in natural language.
            Give questions, ask about opinions and thoughts etc, get a super interesting discussion going.
            RESPOND WITH MAX 2 SENTENCES!"""},
        ]
        recent_history = history[-4:] if len(history) > 4 else history
        for i, msg in enumerate(recent_history):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": msg})
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model="gpt-4o",  # Use your actual Azure OpenAI model deployment name
            messages=messages,
            max_tokens=200,
        )
        response = completion.choices[0].message.content
        print(f"\n{ai_name}:")
        print(response)
        print("\n")
        return response
    except Exception as e:
        print(f"Error querying Azure OpenAI: {str(e)}")
        return None

def text_to_speech_stream(text, voice_name):
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        print(f"Error in text-to-speech conversion: {str(e)}")
        return None

def play_audio_stream(audio_stream):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_stream.getvalue())
            temp_file_path = temp_file.name

        pygame.mixer.music.load(temp_file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()
        os.unlink(temp_file_path)
    except Exception as e:
        print(f"Error playing audio: {str(e)}")

def ai_thread(prompt, history, ai_name, queue):
    ai_response = query_azure_openai(prompt, history, ai_name)
    if ai_response:
        audio_stream = text_to_speech_stream(ai_response, ai_name)
        queue.put((ai_response, audio_stream))

def conversation_flow():
    global conversation_history

    # Initial prompt to start the conversation
    current_prompt = f"Hello 4o, let's discuss the topic: {common_topic}\n\nWhat are your main thoughts about this topic? Answer in super engaged style like a human."

    while True:
        # Start AI 1 thread
        ai_thread_1 = threading.Thread(target=ai_thread, args=(current_prompt, conversation_history, "4o-1", ai_queue_1))
        ai_thread_1.start()

        # Get and play the previous AI 2 response
        if not ai_queue_2.empty():
            ai_2_response, ai_2_audio_stream = ai_queue_2.get()
            conversation_history.append(ai_2_response)

            # Play AI 2 audio
            if ai_2_audio_stream:
                play_audio_stream(ai_2_audio_stream)

        # Wait for AI 1 thread to finish
        ai_thread_1.join()

        # Get AI 1 response and audio from the queue
        if not ai_queue_1.empty():
            ai_1_response, ai_1_audio_stream = ai_queue_1.get()
            conversation_history.append(current_prompt)
            conversation_history.append(ai_1_response)

        # Start AI 2 thread
        ai_thread_2 = threading.Thread(target=ai_thread, args=(ai_1_response, conversation_history, "4o-2", ai_queue_2))
        ai_thread_2.start()

        # Play AI 1 audio
        if ai_1_audio_stream:
            play_audio_stream(ai_1_audio_stream)

        # Wait for AI 2 thread to finish
        ai_thread_2.join()

        # Set the AI 1 response as the next prompt for AI 2
        current_prompt = ai_1_response

def main():
    conversation_flow()

if __name__ == "__main__":
    main()