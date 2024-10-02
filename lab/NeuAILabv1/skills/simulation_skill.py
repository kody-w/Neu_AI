from skills.basic_skill import BasicSkill
import json
import random
from datetime import datetime

class SimulationSkill(BasicSkill):
    def __init__(self):
        self.name = "Simulation"
        self.metadata = {
            "name": self.name,
            "description": "Simulates scenarios or outcomes based on provided parameters and past experiences.",
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
                    }
                },
                "required": ["scenario"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.memory_file = "memory.json"
        self.simulation_log_file = "simulation_log.json"

    def perform(self, scenario, parameters=None, num_simulations=1):
        try:
            past_experiences = self.load_memories()
            simulation_results = self.run_simulations(scenario, parameters, past_experiences, num_simulations)
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

    def run_simulations(self, scenario, parameters, past_experiences, num_simulations):
        results = []
        for _ in range(num_simulations):
            outcome = self.simulate_scenario(scenario, parameters, past_experiences)
            results.append(outcome)
        return results

    def simulate_scenario(self, scenario, parameters, past_experiences):
        relevant_experiences = [exp for exp in past_experiences.values() if scenario.lower() in exp['theme'].lower()]
        
        if not relevant_experiences:
            return {"outcome": "Unknown", "confidence": 0.1}
        
        possible_outcomes = [exp['message'] for exp in relevant_experiences]
        outcome = random.choice(possible_outcomes)
        
        confidence = min(len(relevant_experiences) / 10, 0.9)
        if parameters:
            # Adjust confidence based on parameter matching
            param_match = sum(1 for param, value in parameters.items() if param in outcome.lower())
            confidence += 0.1 * (param_match / len(parameters))
        
        return {"outcome": outcome, "confidence": round(confidence, 2)}

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