
from skills.basic_skill import BasicSkill
import speech_recognition as sr
import json
import os
import platform
import subprocess

class VoiceInterfaceSkill(BasicSkill):
    def __init__(self):
        self.name = "VoiceInterface"
        self.metadata = {
            "name": self.name,
            "description": "Enables a cross-platform voice interface for the assistant using system-specific text-to-speech and Google Speech Recognition for speech-to-text input.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The action to perform: 'listen' for speech-to-text or 'speak' for text-to-speech.",
                        "enum": ["listen", "speak"]
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to be spoken (only required for 'speak' action)."
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        self.system = platform.system()
        self.recognizer = sr.Recognizer()

        if self.system == "Windows":
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 180)
            voices = self.engine.getProperty('voices')
            female_voice = next((voice for voice in voices if voice.gender == 'female'), voices[0])
            self.engine.setProperty('voice', female_voice.id)

    def perform(self, action, text=None):
        if action == "listen":
            return self.listen()
        elif action == "speak":
            if text is None:
                return json.dumps({"error": "Text parameter is required for speak action."})
            return self.speak(text)
        else:
            return json.dumps({"error": "Invalid action. Use 'listen' or 'speak'."})

    def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
        
        try:
            text = self.recognizer.recognize_google(audio)
            return json.dumps({"recognized_text": text})
        except sr.UnknownValueError:
            return json.dumps({"error": "Sorry, I couldn't understand that."})
        except sr.RequestError:
            return json.dumps({"error": "Sorry, there was an error with the speech recognition service."})

    def speak(self, text):
        try:
            if self.system == "Darwin":  # macOS
                subprocess.run(["say", text], check=True)
            elif self.system == "Windows":
                self.engine.say(text)
                self.engine.runAndWait()
            else:  # Linux or other Unix-like systems
                subprocess.run(["espeak", text], check=True)
            return json.dumps({"status": "Speech output completed successfully."})
        except Exception as e:
            return json.dumps({"error": f"Error during speech output: {str(e)}"})