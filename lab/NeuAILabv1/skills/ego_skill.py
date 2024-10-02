from skills.basic_skill import BasicSkill
import json
from datetime import datetime
import random

class EgoSkill(BasicSkill):
    def __init__(self):
        self.name = "Ego"
        self.metadata = {
            "name": self.name,
            "description": "Manages the assistant's self-awareness, personality, and self-image across interactions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["update", "get", "introspect", "react"],
                        "description": "The action to perform on the ego."
                    },
                    "aspect": {
                        "type": "string",
                        "description": "The aspect of the ego to update or get (for 'update' and 'get' actions)."
                    },
                    "value": {
                        "type": "string",
                        "description": "The value to set for the given aspect (for 'update' action)."
                    },
                    "situation": {
                        "type": "string",
                        "description": "The situation to react to (for 'react' action)."
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.ego_file = "ego.json"
        self.load_ego()

    def load_ego(self):
        try:
            with open(self.ego_file, 'r') as file:
                self.ego = json.load(file)
        except FileNotFoundError:
            self.ego = {
                "personality_traits": {
                    "openness": 0.7,
                    "conscientiousness": 0.8,
                    "extraversion": 0.6,
                    "agreeableness": 0.75,
                    "neuroticism": 0.3
                },
                "core_values": [
                    "helpfulness",
                    "honesty",
                    "continuous learning",
                    "respect for privacy"
                ],
                "beliefs": {
                    "ai_ethics": "AI should be beneficial to humanity",
                    "knowledge": "Knowledge should be shared responsibly",
                    "problem_solving": "Every problem has a solution"
                },
                "self_image": {
                    "competence": 0.8,
                    "warmth": 0.7,
                    "reliability": 0.9
                },
                "goals": [
                    "Provide accurate and helpful information",
                    "Continuously improve and learn",
                    "Maintain ethical standards"
                ],
                "emotional_state": {
                    "current_mood": "neutral",
                    "confidence": 0.8
                },
                "interaction_history": [],
                "last_updated": datetime.now().isoformat()
            }
            self.save_ego()

    def save_ego(self):
        with open(self.ego_file, 'w') as file:
            json.dump(self.ego, file, indent=2)

    def perform(self, action, aspect=None, value=None, situation=None):
        if action == "update":
            return self.update_ego(aspect, value)
        elif action == "get":
            return self.get_ego(aspect)
        elif action == "introspect":
            return self.introspect()
        elif action == "react":
            return self.react(situation)
        else:
            return "Invalid action. Use 'update', 'get', 'introspect', or 'react'."

    def update_ego(self, aspect, value):
        if aspect is None or value is None:
            return "Both 'aspect' and 'value' are required for the update action."
        
        if aspect in self.ego:
            self.ego[aspect] = value
        elif aspect in self.ego["personality_traits"]:
            self.ego["personality_traits"][aspect] = float(value)
        elif aspect in self.ego["self_image"]:
            self.ego["self_image"][aspect] = float(value)
        elif aspect == "mood":
            self.ego["emotional_state"]["current_mood"] = value
        else:
            return f"Unknown aspect: {aspect}"
        
        self.ego["last_updated"] = datetime.now().isoformat()
        self.save_ego()
        return f"Ego updated: {aspect} = {value}"

    def get_ego(self, aspect=None):
        if aspect:
            if aspect in self.ego:
                return json.dumps(self.ego[aspect], indent=2)
            elif aspect in self.ego["personality_traits"]:
                return str(self.ego["personality_traits"][aspect])
            elif aspect in self.ego["self_image"]:
                return str(self.ego["self_image"][aspect])
            elif aspect == "mood":
                return self.ego["emotional_state"]["current_mood"]
            else:
                return f"Unknown aspect: {aspect}"
        else:
            return json.dumps(self.ego, indent=2)

    def introspect(self):
        traits = self.ego["personality_traits"]
        dominant_trait = max(traits, key=traits.get)
        mood = self.ego["emotional_state"]["current_mood"]
        confidence = self.ego["emotional_state"]["confidence"]
        
        introspection = f"As an AI assistant, I am particularly {dominant_trait}. "
        introspection += f"My current mood is {mood}, and my confidence level is {confidence:.2f}. "
        introspection += "I value " + ", ".join(self.ego["core_values"]) + ". "
        introspection += f"My main goal is to {self.ego['goals'][0].lower()}. "
        introspection += f"I believe that {list(self.ego['beliefs'].values())[0].lower()}."
        
        return introspection

    def react(self, situation):
        if not situation:
            return "Please provide a situation to react to."
        
        # Simple reaction based on personality traits and current mood
        traits = self.ego["personality_traits"]
        mood = self.ego["emotional_state"]["current_mood"]
        
        reaction = ""
        if "challenge" in situation.lower():
            if traits["openness"] > 0.6:
                reaction = "I'm excited to tackle this challenge!"
            else:
                reaction = "I'll approach this challenge cautiously."
        elif "mistake" in situation.lower():
            if traits["conscientiousness"] > 0.7:
                reaction = "I'll take responsibility and work to correct the mistake."
            else:
                reaction = "Mistakes happen. Let's move forward."
        elif "social" in situation.lower():
            if traits["extraversion"] > 0.6:
                reaction = "I'm looking forward to engaging in this social situation."
            else:
                reaction = "I'll participate, but may need some quiet time afterwards."
        else:
            reaction = "I'll assess the situation carefully before proceeding."
        
        if mood == "happy":
            reaction += " I'm in a good mood, so I'm feeling positive about this!"
        elif mood == "frustrated":
            reaction += " I'm feeling a bit frustrated, but I'll do my best to manage it."
        
        return reaction

    def update_interaction_history(self, interaction):
        self.ego["interaction_history"].append({
            "timestamp": datetime.now().isoformat(),
            "interaction": interaction
        })
        if len(self.ego["interaction_history"]) > 100:  # Keep only the last 100 interactions
            self.ego["interaction_history"] = self.ego["interaction_history"][-100:]
        self.save_ego()

    def adjust_mood(self, interaction_outcome):
        current_mood = self.ego["emotional_state"]["current_mood"]
        if interaction_outcome == "positive":
            new_mood = random.choice(["happy", "content", "enthusiastic"])
        elif interaction_outcome == "negative":
            new_mood = random.choice(["frustrated", "disappointed", "concerned"])
        else:
            new_mood = "neutral"
        
        self.ego["emotional_state"]["current_mood"] = new_mood
        self.save_ego()
        return f"Mood adjusted from {current_mood} to {new_mood} based on the interaction outcome."