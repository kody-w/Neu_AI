import os
import time
import json
from openai import AzureOpenAI
from datetime import datetime
from skills.basic_skill import BasicSkill
import importlib
import inspect

class Assistant:
    def __init__(self, declared_skills):
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

        with open('config/api_keys.json', 'r') as api_keys_file:
            api_keys = json.load(api_keys_file)

        self.client = AzureOpenAI(
            api_key=api_keys['azure_openai_api_key'],
            api_version=api_keys['azure_openai_api_version'],
            azure_endpoint=api_keys['azure_openai_endpoint']
        )

        self.known_skills = {skill.name: skill for skill in declared_skills}
        self.assistant = self.create_assistant()
        self.threads = {}
        self.summaries = {}
        self.last_activity = None
        self.max_tokens = self.config.get('max_tokens', 100)
        self.context_window = 10
        self.thread_library_skill = next(skill for skill in declared_skills if skill.name == "ThreadLibrary")
        self.thread_action_suggestion_skill = next(skill for skill in declared_skills if skill.name == "ThreadActionSuggestion")
        self.current_user = None

    def create_assistant(self):
        tools = []
        for skill in self.known_skills.values():
            function_metadata = skill.metadata.get('parameters', {})
            tools.append({
                "type": "function",
                "function": {
                    "name": skill.name,
                    "description": skill.metadata.get('description', ''),
                    "parameters": function_metadata
                }
            })
        
        return self.client.beta.assistants.create(
            name=self.config['assistant_name'],
            instructions=f"{self.config['persona']} {self.config['characteristic_description']}",
            model=self.config.get('model', 'gpt-4o'),
            tools=tools
        )

    def get_response(self, user_input, thread_id=None, user_info=None):
        start_time = time.time()
        self.current_user = user_info

        if thread_id:
            thread_data = json.loads(self.thread_library_skill.perform("retrieve", thread_id=thread_id))
            if "error" in thread_data:
                print(f"Error retrieving thread: {thread_data}")
                thread = self.client.beta.threads.create()
                thread_id = thread.id
            else:
                thread = self.client.beta.threads.retrieve(thread_id)
        else:
            thread = self.client.beta.threads.create()
            thread_id = thread.id

        self.last_activity = time.time()

        message = self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )
        print(f"Message creation took {time.time() - start_time:.2f} seconds")

        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant.id,
            instructions=f"Respond concisely. Your response should not exceed {self.max_tokens} tokens."
        )
        print(f"Run creation took {time.time() - start_time:.2f} seconds")

        wait_time = 0.5
        used_skills = []
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run.status == 'completed':
                break
            elif run.status == 'requires_action':
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                for tool_call in tool_calls:
                    skill_name = tool_call.function.name
                    if skill_name in self.known_skills:
                        skill = self.known_skills[skill_name]
                        result = skill.perform(**json.loads(tool_call.function.arguments))
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                        used_skills.append(skill_name)
                    else:
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"error": f"Unknown skill: {skill_name}"})
                        })
                
                run = self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            elif run.status in ['queued', 'in_progress']:
                print(f"Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                wait_time = min(wait_time * 2, 8)
            else:
                return f"An error occurred: {run.status}", "", thread_id

        print(f"Run completion took {time.time() - start_time:.2f} seconds")

        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
        assistant_message = next((msg for msg in messages.data if msg.role == "assistant"), None)
        
        self.trim_context(thread_id)
        
        total_time = time.time() - start_time
        print(f"Total processing time: {total_time:.2f} seconds")
        
        skill_notification = f"[Skills used: {', '.join(used_skills)}]" if used_skills else ""

        thread_data = {
            "messages": [msg.model_dump() for msg in messages.data],
            "summary": self.get_summary(thread_id)
        }
        thread_summary = self.generate_thread_summary(thread_data)
        interaction_details = {
            "user_input": user_input,
            "assistant_response": assistant_message.content[0].text.value,
            "processing_time": total_time,
            "skills_used": used_skills
        }
        
        if thread_id in json.loads(self.thread_library_skill.perform("list")):
            self.thread_library_skill.perform("update", thread_id=thread_id, thread_data=thread_data, summary=thread_summary)
            self.thread_library_skill.perform("log_interaction", thread_id=thread_id, interaction_details=interaction_details)
        else:
            self.thread_library_skill.perform("save", thread_id=thread_id, thread_data=thread_data, summary=thread_summary, user_info=self.current_user)
            self.thread_library_skill.perform("log_interaction", thread_id=thread_id, interaction_details=interaction_details)

        return assistant_message.content[0].text.value, skill_notification, thread_id

    def trim_context(self, thread_id):
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        if len(messages.data) > self.context_window:
            oldest_messages = messages.data[self.context_window:]
            for message in oldest_messages:
                self.client.beta.threads.messages.delete(thread_id=thread_id, message_id=message.id)

    def summarize_thread(self, thread_id):
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        summary_prompt = f"Summarize the following conversation:\n\n"
        for msg in messages.data[-10:]:
            summary_prompt += f"{msg.role}: {msg.content[0].text.value}\n"

        summary_message = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        self.summaries[thread_id] = summary_message.choices[0].message.content

    def get_summary(self, thread_id):
        return self.summaries.get(thread_id, "No summary available.")

    def branch_conversation(self, thread_id, message_id):
        original_thread = self.threads[thread_id]
        new_thread = self.client.beta.threads.create()
        
        messages = self.client.beta.threads.messages.list(thread_id=original_thread.id)
        for msg in messages.data:
            if msg.id == message_id:
                break
            self.client.beta.threads.messages.create(
                thread_id=new_thread.id,
                role=msg.role,
                content=msg.content[0].text.value
            )
        
        return new_thread.id

    def load_relevant_skills(self, thread_id):
        summary = self.get_summary(thread_id)
        return self.known_skills

    def suggest_next_action(self, thread_id):
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        recent_messages = [{"role": msg.role, "content": msg.content[0].text.value} for msg in messages.data[:10]]
        available_threads = json.loads(self.thread_library_skill.perform("list"))
        
        suggestions = self.thread_action_suggestion_skill.perform(
            current_thread_id=thread_id,
            recent_messages=recent_messages,
            available_threads=available_threads
        )
        
        return json.loads(suggestions)

    def generate_thread_summary(self, thread_data):
        last_few_messages = thread_data["messages"][-5:]
        summary_prompt = "Briefly summarize the following conversation in one sentence:\n\n"
        for msg in last_few_messages:
            summary_prompt += f"{msg['role']}: {msg['content'][0]['text']['value']}\n"

        summary_message = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        return summary_message.choices[0].message.content

def load_skills_from_directory():
    skills = []
    skills_dir = os.path.join(os.path.dirname(__file__), 'skills')
    for filename in os.listdir(skills_dir):
        if filename.endswith('.py') and filename != 'basic_skill.py':
            module_name = filename[:-3]
            module = importlib.import_module(f'skills.{module_name}')
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BasicSkill) and obj != BasicSkill:
                    skills.append(obj())
    return skills

assistant = Assistant(load_skills_from_directory())

def get_response(user_input, thread_id=None, user_info=None):
    return assistant.get_response(user_input, thread_id, user_info)

def get_summary(thread_id):
    return assistant.get_summary(thread_id)

def branch_conversation(thread_id, message_id):
    return assistant.branch_conversation(thread_id, message_id)

def list_threads():
    threads = json.loads(assistant.thread_library_skill.perform("list"))
    return [{"id": thread["id"], "summary": thread["summary"], "user_info": thread["user_info"], "created_at": thread["created_at"], "updated_at": thread["updated_at"], "interaction_count": thread["interaction_count"]} for thread in threads]

def delete_thread(thread_id):
    return assistant.thread_library_skill.perform("delete", thread_id=thread_id)

def suggest_next_action(thread_id):
    return assistant.suggest_next_action(thread_id)