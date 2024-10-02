from skills.basic_skill import BasicSkill
import json
import os
import autogen
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GroqAutoGenGroupGeneratorSkill(BasicSkill):
    def __init__(self):
        self.name = 'GroqAutoGenGroupGenerator'
        self.metadata = {
            "name": self.name,
            "description": "Generates AutoGen groups using Groq API based on the given task and produces a .txt file as the final deliverable.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The task description for the AutoGen group to work on."
                    },
                    "num_agents": {
                        "type": "integer",
                        "description": "The number of agents to include in the AutoGen group."
                    },
                    "max_turns": {
                        "type": "integer",
                        "description": "The maximum number of conversation turns for the AutoGen group."
                    },
                    "output_file": {
                        "type": "string",
                        "description": "The name of the output .txt file to be generated."
                    }
                },
                "required": ["task", "num_agents", "max_turns", "output_file"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, task, num_agents, max_turns, output_file):
        try:
            # Get Groq API key and model
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables.")
            model = os.getenv('LLM_MODEL', 'llama3-groq-70b-8192-tool-use-preview')

            # Create Groq configuration
            groq_config = {
                "cache_seed": 42,
                "config_list": [{
                    "model": model,
                    "api_key": groq_api_key,
                    "base_url": "https://api.groq.com/openai/v1"
                }],
                "temperature": 0.7,
                "max_tokens": 2000,
            }

            # Create facilitator agent
            facilitator = autogen.AssistantAgent(
                name="Facilitator",
                system_message=f"""You are the facilitator overseeing the AutoGen group working on: {task}.
                Your role is to:
                1. Guide the discussion and ensure all aspects of the task are covered.
                2. Encourage contributions from all group members.
                3. Summarize key points and decisions made during the discussion.
                4. Keep the group focused and on-track to complete the task within {max_turns - 1} turns.
                5. In the final turn, instruct the Report Compiler to create the final deliverable.""",
                llm_config=groq_config,
            )

            # Create worker agents
            agents = [
                autogen.AssistantAgent(
                    name=f"Agent_{i+1}",
                    system_message=f"""You are Agent_{i+1} in the AutoGen group. Your task is to contribute to: {task}.
                    Provide specific, actionable ideas and engage in productive discussion with other agents.
                    Be creative, think critically, and build upon others' ideas.""",
                    llm_config=groq_config,
                ) for i in range(num_agents)
            ]

            # Create report compiler agent
            report_compiler = autogen.AssistantAgent(
                name="ReportCompiler",
                system_message=f"""You are the Report Compiler for the AutoGen group.
                Your role is to:
                1. Observe the entire discussion.
                2. When instructed by the Facilitator in the final turn, compile a comprehensive report based on the group's discussion.
                3. Ensure the report is well-structured, detailed, and addresses all aspects of the task.
                4. Use appropriate headings and subheadings to organize the information.
                5. Include an executive summary at the beginning of the report.
                6. Begin your response with 'FINAL REPORT:' to clearly mark the start of the deliverable.""",
                llm_config=groq_config,
            )

            # Create user proxy with Docker disabled
            user_proxy = autogen.UserProxyAgent(
                name="UserProxy",
                system_message="You are coordinating the AutoGen group. Do not provide any input unless explicitly asked.",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=max_turns,
                code_execution_config={"use_docker": False}
            )

            # Create group chat
            groupchat = autogen.GroupChat(agents=[facilitator, report_compiler] + agents + [user_proxy], messages=[], max_round=max_turns)
            group_manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=groq_config)

            # Initiate the chat
            initial_message = f"""Let's work on the following task: {task}. 
            Facilitator, please guide the discussion to ensure we create a comprehensive solution. 
            Remember, we have {max_turns - 1} turns for discussion, and the final turn will be used to compile the report.
            In the last turn, Facilitator, please instruct the ReportCompiler to generate the final report."""
            
            result = group_manager.initiate_chat(user_proxy, message=initial_message)

            # Extract the final deliverable from the chat history
            final_deliverable = self.extract_deliverable(result.chat_history)

            # Write the final deliverable to a .txt file
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_file)
            with open(output_path, "w") as f:
                f.write(final_deliverable)

            return f"AutoGen group has completed the task using Groq API. The final deliverable has been saved to {output_path}"
        except Exception as e:
            logger.error(f"An error occurred in GroqAutoGenGroupGeneratorSkill: {str(e)}")
            return f"An error occurred while generating the AutoGen group: {str(e)}"

    def extract_deliverable(self, chat_history):
        for message in reversed(chat_history):
            if message.get('role') == 'assistant' and message.get('name') == 'ReportCompiler' and 'FINAL REPORT:' in message.get('content', ''):
                return message.get('content').split('FINAL REPORT:', 1)[1].strip()
        
        # If no final report is found, compile a summary from the discussion
        summary = "Executive Summary:\n\n"
        for message in chat_history:
            if message.get('role') == 'assistant' and message.get('name') != 'ReportCompiler':
                summary += f"{message.get('name')}: {message.get('content')}\n\n"
        
        return summary if summary != "Executive Summary:\n\n" else "No final report found in the chat history."