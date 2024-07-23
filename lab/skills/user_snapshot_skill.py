from skills.basic_skill import BasicSkill
import os
import base64
from openai import AzureOpenAI
import json
import requests
from PIL import Image, ImageGrab
import io
from datetime import datetime
import speech_recognition as sr
import time

# Try to import OpenCV, but don't fail if it's not installed
try:
    import cv2
    WEBCAM_AVAILABLE = True
except ImportError:
    WEBCAM_AVAILABLE = False

class UserSnapshotAnalysisSkill(BasicSkill):
    def __init__(self):
        self.name = "UserSnapshotAnalysis"
        self.metadata = {
            "name": self.name,
            "description": "Captures a snapshot of the user (via webcam or screenshot) and analyzes it using GPT-4 Vision API to describe who the assistant is talking to.",
            "parameters": {
                "type": "object",
                "properties": {
                    "capture_method": {
                        "type": "string",
                        "enum": ["webcam", "screenshot"],
                        "description": "Method to capture the user's image: 'webcam' or 'screenshot'"
                    }
                },
                "required": ["capture_method"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        # Load API configuration
        with open('config/api_keys.json', 'r') as api_keys_file:
            api_keys = json.load(api_keys_file)

        self.api_key = api_keys['azure_openai_api_key']
        self.endpoint = f"{api_keys['azure_openai_endpoint']}openai/deployments/gpt-4o/chat/completions?api-version={api_keys['azure_openai_api_version']}"

        # Ensure the images directory exists
        self.images_dir = os.path.join(os.getcwd(), 'user_snapshots')
        os.makedirs(self.images_dir, exist_ok=True)

        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()

    def perform(self, capture_method):
        if capture_method == 'webcam':
            if WEBCAM_AVAILABLE:
                encoded_image, saved_image_path = self.capture_from_webcam()
                print(f"Webcam image saved at: {saved_image_path}")
            else:
                return "Webcam functionality is not available. Please install opencv-python to use this feature."
        elif capture_method == 'screenshot':
            encoded_image, saved_image_path = self.capture_screenshot_with_voice_command()
            print(f"Screenshot saved at: {saved_image_path}")
        else:
            return "Invalid capture method. Please use 'webcam' or 'screenshot'."

        analysis = self.analyze_image(encoded_image)
        return f"Image captured and saved at: {saved_image_path}\n\nAnalysis: {analysis}"

    def capture_from_webcam(self):
        if not WEBCAM_AVAILABLE:
            raise ImportError("OpenCV is not installed. Cannot use webcam functionality.")

        cap = cv2.VideoCapture(0)  # 0 is usually the default webcam
        if not cap.isOpened():
            raise IOError("Cannot open webcam")

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise IOError("Failed to capture image from webcam")

        # Convert the image from BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_frame)

        return self.save_and_encode_image(pil_image, "webcam_snapshot")

    def capture_screenshot_with_voice_command(self):
        print("Please say 'capture' when you're ready to take the screenshot.")
        
        while True:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                print("Listening for voice command...")
                try:
                    audio = self.recognizer.listen(source, timeout=5)
                    command = self.recognizer.recognize_google(audio).lower()
                    print(f"Recognized: {command}")
                    
                    if 'capture' in command:
                        print("Capturing screenshot...")
                        screenshot = ImageGrab.grab()
                        return self.save_and_encode_image(screenshot, "screenshot_snapshot")
                    else:
                        print("Command not recognized. Please say 'capture' to take a screenshot.")
                except sr.UnknownValueError:
                    print("Could not understand audio. Please try again.")
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")
                except Exception as e:
                    print(f"An error occurred: {e}")
                
                time.sleep(1)  # Short delay before listening again

    def save_and_encode_image(self, pil_image, prefix):
        # Convert to RGB if the image is in RGBA mode
        if pil_image.mode == 'RGBA':
            pil_image = pil_image.convert('RGB')

        # Save the image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"{prefix}_{timestamp}.jpg"
        image_path = os.path.join(self.images_dir, image_filename)
        pil_image.save(image_path, 'JPEG')

        # Convert PIL Image to bytes
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        return base64.b64encode(img_byte_arr).decode('ascii'), image_path

    def analyze_image(self, encoded_image):
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are an AI assistant that analyzes images of users and provides detailed descriptions of who the assistant is talking to. Focus on describing the person's appearance, estimated age, gender, clothing, and any notable features or expressions. Do not attempt to identify specific individuals by name."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Analyze this image and provide a detailed description of the person I'm talking to."
                        }
                    ]
                }
            ],
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 800
        }

        try:
            response = requests.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.RequestException as e:
            return f"Failed to analyze the image. Error: {str(e)}"