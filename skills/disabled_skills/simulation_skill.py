from skills.basic_skill import BasicSkill
import json
import random
from datetime import datetime
import autogen
from openai import AzureOpenAI

class SimulationSkill(BasicSkill):
    def __init__(self):
        self.name = "Simulation"
        self.metadata = {
            "name": self.name,
            "description": "Simulates scenarios or outcomes using AutoGen agents for high-fidelity simulations based on provided parameters and past experiences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "string",
                        "description": "The scenario to simulate"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Additional parameters for the simulation"
                    },
                    "num_simulations": {
                        "type": "integer",
                        "description": "Number of simulation runs to perform"
                    },
                    "agents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "role": {"type": "string"},
                                "goals": {"type": "array", "items": {"type": "string"}},
                                "constraints": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["name", "role"]
                        },
                        "description": "List of agents to participate in the simulation"
                    },
                    "max_turns": {
                        "type": "integer",
                        "description": "Maximum number of interaction turns in the simulation",
                        "default": 10
                    }
                },
                "required": ["scenario", "agents"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.memory_file = "memory.json"
        self.simulation_log_file = "simulation_log.json"
        self.api_keys = self.load_api_keys()

    def load_api_keys(self, api_keys_path='config/api_keys.json'):
        try:
            with open(api_keys_path, 'r') as api_keys_file:
                return json.load(api_keys_file)
        except FileNotFoundError:
            raise Exception(f"Error: API keys file '{api_keys_path}' not found.")
        except json.JSONDecodeError:
            raise Exception(f"Error: Invalid JSON in API keys file '{api_keys_path}'.")

    def perform(self, scenario, agents, parameters=None, num_simulations=1, max_turns=10):
        try:
            past_experiences = self.load_memories()
            simulation_results = self.run_simulations(scenario, agents, parameters, past_experiences, num_simulations, max_turns)
            self.log_simulation(scenario, parameters, simulation_results)
            return self.analyze_results(simulation_results)
        except Exception as e:
            return f"An error occurred during simulation: {str(e)}"

    def load_memories(self):
        try:
            with open(self.memory_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def run_simulations(self, scenario, agents, parameters, past_experiences, num_simulations, max_turns):
        results = []
        for _ in range(num_simulations):
            outcome = self.simulate_scenario_with_agents(scenario, agents, parameters, past_experiences, max_turns)
            results.append(outcome)
        return results

    def simulate_scenario_with_agents(self, scenario, agents, parameters, past_experiences, max_turns):
        client = AzureOpenAI(
            api_key=self.api_keys['azure_openai_api_key'],
            api_version=self.api_keys['azure_openai_api_version'],
            azure_endpoint=self.api_keys['azure_openai_endpoint']
        )

        def get_llm_config(agent_config):
            return {
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 2000,
                "azure_deployment": "gpt-4o",
                "azure_endpoint": self.api_keys['azure_openai_endpoint'],
                "api_key": self.api_keys['azure_openai_api_key'],
                "api_type": "azure",
                "api_version": self.api_keys['azure_openai_api_version']
            }

        simulation_agents = []
        for agent_config in agents:
            llm_config = get_llm_config(agent_config)
            agent = autogen.AssistantAgent(
                name=agent_config['name'],
                system_message=f"You are {agent_config['role']}. Goals: {', '.join(agent_config.get('goals', []))}. Constraints: {', '.join(agent_config.get('constraints', []))}",
                llm_config=llm_config,
            )
            simulation_agents.append(agent)

        user_proxy = autogen.UserProxyAgent(
            name="SimulationController",
            system_message="You are controlling the simulation. Observe and guide the agents if necessary.",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=max_turns,
            code_execution_config={"use_docker": False}  # Disable Docker usage
        )

        group_chat = autogen.GroupChat(agents=simulation_agents, messages=[], max_round=max_turns)
        manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=get_llm_config({}))

        # Incorporate past experiences into the scenario
        relevant_experiences = [exp for exp in past_experiences.values() if scenario.lower() in exp['theme'].lower()]
        experience_context = "\n".join([exp['message'] for exp in relevant_experiences[:5]])  # Use top 5 relevant experiences

        # Construct the initial message for the simulation
        initial_message = f"""
        Scenario: {scenario}
        Parameters: {json.dumps(parameters) if parameters else 'None'}
        Past Experiences:
        {experience_context}

        Begin the simulation based on this scenario and context. Each agent should act according to their role, goals, and constraints.
        """

        # Run the simulation
        result = manager.initiate_chat(user_proxy, message=initial_message)

        # Extract the outcome from the simulation result
        simulated_outcome = self.extract_outcome_from_chat(result)

        # Calculate confidence based on the depth and relevance of the simulation
        confidence = min(len(group_chat.messages) / max_turns, 0.9)
        if parameters:
            param_relevance = sum(1 for param, value in parameters.items() if param.lower() in simulated_outcome.lower())
            confidence += 0.1 * (param_relevance / len(parameters))

        return {"outcome": simulated_outcome, "confidence": round(confidence, 2)}

    def extract_outcome_from_chat(self, chat_result):
        # This is a simplified extraction. You might want to implement a more sophisticated method
        # to summarize the chat and extract the key outcomes.
        last_messages = chat_result[-5:]  # Consider the last 5 messages
        return " ".join([msg['content'] for msg in last_messages if msg['content']])

    def analyze_results(self, results):
        outcomes = {}
        for result in results:
            outcome = result['outcome']
            if outcome in outcomes:
                outcomes[outcome]['count'] += 1
                outcomes[outcome]['total_confidence'] += result['confidence']
            else:
                outcomes[outcome] = {'count': 1, 'total_confidence': result['confidence']}

        analysis = []
        for outcome, data in outcomes.items():
            probability = data['count'] / len(results)
            avg_confidence = data['total_confidence'] / data['count']
            analysis.append({
                "outcome": outcome,
                "probability": round(probability, 2),
                "average_confidence": round(avg_confidence, 2)
            })

        return sorted(analysis, key=lambda x: x['probability'], reverse=True)

    def log_simulation(self, scenario, parameters, results):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "scenario": scenario,
            "parameters": parameters,
            "results": results
        }
        try:
            with open(self.simulation_log_file, 'r+') as file:
                log = json.load(file)
                log.append(log_entry)
                file.seek(0)
                json.dump(log, file, indent=2)
        except FileNotFoundError:
            with open(self.simulation_log_file, 'w') as file:
                json.dump([log_entry], file, indent=2)

# End of SimulationSkill class