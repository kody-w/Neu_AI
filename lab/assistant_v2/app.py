from openai_handler import get_response, get_summary, branch_conversation, list_threads, delete_thread, suggest_next_action, assistant
import time
import threading
import sys
import json
from datetime import datetime
import uuid

def spinner(stop):
    spinner_chars = ['|', '/', '-', '\\']
    i = 0
    while not stop.is_set():
        sys.stdout.write(f"\rThinking {spinner_chars[i]}")
        sys.stdout.flush()
        i = (i + 1) % len(spinner_chars)
        time.sleep(0.1)

def get_user_info():
    user_id = str(uuid.uuid4())
    username = input("Please enter your name: ")
    return {
        "user_id": user_id,
        "username": username,
        "session_start": datetime.now().isoformat()
    }

def chat():
    print(f"Welcome to {assistant.config['assistant_name']}, your AI assistant!")
    user_info = get_user_info()
    print(f"Hello, {user_info['username']}!")
    print(f"Available skills: {', '.join(assistant.known_skills.keys())}")
    print("Commands:")
    print("  'exit' to end the conversation")
    print("  'summary' to get a conversation summary")
    print("  'branch <message_id>' to create a new conversation branch")
    print("  'list threads' to see all saved threads")
    print("  'switch <thread_id>' to switch to a different thread")
    print("  'delete thread <thread_id>' to delete a thread")
    print("  'suggest' to get suggestions for the next action")

    current_thread_id = None

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'exit':
            print(f"{assistant.config['assistant_name']}: Goodbye!")
            break
        elif user_input.lower() == 'summary':
            if current_thread_id:
                print(get_summary(current_thread_id))
            else:
                print("No active conversation to summarize.")
            continue
        elif user_input.lower().startswith('branch '):
            if current_thread_id:
                message_id = user_input.split()[1]
                new_thread_id = branch_conversation(current_thread_id, message_id)
                print(f"Created new conversation branch. New thread ID: {new_thread_id}")
                current_thread_id = new_thread_id
            else:
                print("No active conversation to branch from.")
            continue
        elif user_input.lower() == 'list threads':
            threads = list_threads()
            for thread in threads:
                created_at = datetime.fromisoformat(thread['created_at']).strftime("%Y-%m-%d %H:%M:%S")
                updated_at = datetime.fromisoformat(thread['updated_at']).strftime("%Y-%m-%d %H:%M:%S")
                print(f"Thread ID: {thread['id']}")
                print(f"Summary: {thread['summary']}")
                print(f"User: {thread['user_info']['username']}")
                print(f"Created at: {created_at}")
                print(f"Last updated: {updated_at}")
                print(f"Interaction count: {thread['interaction_count']}")
                print("-" * 50)
            continue
        elif user_input.lower().startswith('switch '):
            new_thread_id = user_input.split()[1]
            current_thread_id = new_thread_id
            print(f"Switched to thread {current_thread_id}")
            continue
        elif user_input.lower().startswith('delete thread '):
            thread_id = user_input.split()[2]
            result = delete_thread(thread_id)
            print(result)
            if thread_id == current_thread_id:
                current_thread_id = None
            continue
        elif user_input.lower() == 'suggest':
            if current_thread_id:
                suggestions = suggest_next_action(current_thread_id)
                print("Suggested next actions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"{i}. {suggestion}")
            else:
                print("No active conversation. Start a new one or switch to an existing thread.")
            continue
        
        if user_input:
            stop_spinner = threading.Event()
            spinner_thread = threading.Thread(target=spinner, args=(stop_spinner,))
            spinner_thread.start()

            try:
                ai_response, skill_notification, thread_id = get_response(user_input, current_thread_id, user_info)
                current_thread_id = thread_id
            finally:
                stop_spinner.set()
                spinner_thread.join()
                sys.stdout.write('\r' + ' ' * 20 + '\r')  # Clear the spinner line
                sys.stdout.flush()

            print(f"{assistant.config['assistant_name']}: {ai_response}")
            if skill_notification:
                print(skill_notification)

if __name__ == "__main__":
    chat()