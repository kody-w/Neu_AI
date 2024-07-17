from skills.basic_skill import BasicSkill
import re
import json
from datetime import datetime
import random

class UnexpectedInputHandlingSkill(BasicSkill):
    def __init__(self):
        self.name = "UnexpectedInputHandling"
        self.metadata = {
            "name": self.name,
            "description": "Handles unexpected or unusual inputs by analyzing, categorizing, and providing appropriate responses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "The user input to analyze and handle."
                    }
                },
                "required": ["input"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.unexpected_inputs_file = "unexpected_inputs.json"
        self.load_unexpected_inputs()

    def load_unexpected_inputs(self):
        try:
            with open(self.unexpected_inputs_file, 'r') as file:
                self.unexpected_inputs = json.load(file)
        except FileNotFoundError:
            self.unexpected_inputs = []
        self.save_unexpected_inputs()

    def save_unexpected_inputs(self):
        with open(self.unexpected_inputs_file, 'w') as file:
            json.dump(self.unexpected_inputs, file, indent=2)

    def perform(self, input):
        analysis = self.analyze_input(input)
        response = self.generate_response(analysis)
        self.log_unexpected_input(input, analysis)
        return response

    def analyze_input(self, input):
        analysis = {
            "length": len(input),
            "word_count": len(input.split()),
            "contains_numbers": bool(re.search(r'\d', input)),
            "contains_special_chars": bool(re.search(r'[^a-zA-Z0-9\s]', input)),
            "all_caps": input.isupper(),
            "no_spaces": ' ' not in input,
            "starts_with_punctuation": bool(re.match(r'^[^\w\s]', input)),
            "ends_with_punctuation": bool(re.match(r'[^\w\s]$', input)),
            "repeated_characters": bool(re.search(r'(.)\1{2,}', input)),
            "potential_language": self.detect_language(input),
            "sentiment": self.analyze_sentiment(input),
            "category": self.categorize_input(input)
        }
        return analysis

    def detect_language(self, input):
        # This is a simplified language detection.
        # In a real-world scenario, you might want to use a more sophisticated library like langdetect.
        if re.search(r'[α-ωΑ-Ω]', input):
            return "Greek"
        elif re.search(r'[а-яА-Я]', input):
            return "Russian"
        elif re.search(r'[一-龯]', input):
            return "Chinese"
        # Add more language detections as needed
        return "English"  # Default to English

    def analyze_sentiment(self, input):
        # This is a very basic sentiment analysis.
        # In a real-world scenario, you'd want to use a more sophisticated sentiment analysis tool.
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic"]
        negative_words = ["bad", "terrible", "awful", "horrible", "disappointing", "poor"]
        
        input_lower = input.lower()
        positive_count = sum(word in input_lower for word in positive_words)
        negative_count = sum(word in input_lower for word in negative_words)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def categorize_input(self, input):
        if len(input) < 5:
            return "very_short"
        elif input.isupper():
            return "shouting"
        elif re.search(r'(.)\1{3,}', input):
            return "exaggerated"
        elif re.search(r'[^\w\s]', input) and not re.search(r'[a-zA-Z]', input):
            return "symbols_only"
        elif not re.search(r'[a-zA-Z]', input) and re.search(r'\d', input):
            return "numbers_only"
        elif self.detect_language(input) != "English":
            return "foreign_language"
        else:
            return "unusual_content"

    def generate_response(self, analysis):
        category = analysis['category']
        responses = {
            "very_short": [
                "I see you're being concise! Could you elaborate a bit more?",
                "Interesting! Can you expand on that?",
                "Short and sweet! What else can you tell me?"
            ],
            "shouting": [
                "I can hear you loud and clear! No need to shout.",
                "Your message comes across strongly. Is everything okay?",
                "I'm listening attentively, even without the caps lock."
            ],
            "exaggerated": [
                "You seem very enthusiastic! What's got you so excited?",
                "That's quite an emphasis! Tell me more about why this is so important to you.",
                "I can sense your strong feelings about this. Let's discuss it further."
            ],
            "symbols_only": [
                "Interesting use of symbols! What are you trying to express?",
                "I see you're communicating in symbols. Could you clarify your message in words?",
                "Symbols can be powerful! What do these mean to you?"
            ],
            "numbers_only": [
                "I see you're working with numbers. Is this a calculation or code?",
                "Interesting sequence of numbers! What do they represent?",
                "Numbers can tell a story. What's the story behind these?"
            ],
            "foreign_language": [
                "It seems you might be using a language other than English. While I'm trained primarily in English, I'll do my best to understand and assist you.",
                "I detected a different language. Could you try expressing your message in English?",
                "Multilingual communication is fascinating! However, I'm most fluent in English. Could you try rephrasing?"
            ],
            "unusual_content": [
                "That's an interesting perspective! Could you tell me more about what you mean?",
                "I'm intrigued by your unique input. Can you elaborate on your thoughts?",
                "Your message is quite unique. I'd love to understand more about where you're coming from."
            ]
        }
        return random.choice(responses.get(category, ["I'm not sure I understand. Could you rephrase that?"]))

    def log_unexpected_input(self, input, analysis):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "input": input,
            "analysis": analysis
        }
        self.unexpected_inputs.append(log_entry)
        if len(self.unexpected_inputs) > 1000:  # Keep only the last 1000 entries
            self.unexpected_inputs = self.unexpected_inputs[-1000:]
        self.save_unexpected_inputs()