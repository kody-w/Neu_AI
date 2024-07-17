from skills.basic_skill import BasicSkill
import os
import requests
import base64
from openai import AzureOpenAI
import json
from PIL import Image
import io
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
from bs4 import BeautifulSoup
import traceback
import time

class WebsiteScreenshotAnalysisSkill(BasicSkill):
    def __init__(self):
        self.name = "WebsiteScreenshotAnalysis"
        self.metadata = {
            "name": self.name,
            "description": "Analyzes websites using various methods including screenshots, HTML parsing, and text extraction with multiple fallback options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the website to analyze."
                    }
                },
                "required": ["url"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        # Set up logging
        logging.basicConfig(filename='website_analysis.log', level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Load API configuration
        try:
            with open('config/api_keys.json', 'r') as api_keys_file:
                api_keys = json.load(api_keys_file)

            self.api_key = api_keys['azure_openai_api_key']
            self.endpoint = f"{api_keys['azure_openai_endpoint']}openai/deployments/gpt-4o/chat/completions?api-version={api_keys['azure_openai_api_version']}"
        except Exception as e:
            self.logger.error(f"Failed to load API keys: {str(e)}")
            raise

        # Ensure the screenshots directory exists
        self.screenshots_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def perform(self, url):
        self.logger.info(f"Starting analysis of {url}")
        try:
            # Attempt to capture and analyze screenshot
            screenshot_path = self.capture_website_screenshot(url)
            if screenshot_path:
                self.logger.info(f"Screenshot captured successfully: {screenshot_path}")
                encoded_image = self.encode_image(screenshot_path)
                analysis = self.analyze_image(encoded_image)
                return f"Visual analysis of {url}:\n\n{analysis}"
            else:
                self.logger.warning("Screenshot capture failed. Falling back to text extraction.")
                
            # Fallback to Selenium-based content extraction
            content = self.extract_content_selenium(url)
            if content:
                self.logger.info("Content extracted using Selenium")
                analysis = self.analyze_text(content)
                return f"Text-based analysis of {url} (Selenium method):\n\n{analysis}"
            else:
                self.logger.warning("Selenium-based extraction failed. Trying requests-based extraction.")
            
            # Fallback to requests-based content extraction
            content = self.extract_content_requests(url)
            if content:
                self.logger.info("Content extracted using requests")
                analysis = self.analyze_text(content)
                return f"Text-based analysis of {url} (requests method):\n\n{analysis}"
            else:
                self.logger.error("All extraction methods failed")
                return f"Failed to analyze {url}. Unable to capture screenshot or extract content using any method."
        except Exception as e:
            self.logger.error(f"Error in perform method: {str(e)}")
            self.logger.error(traceback.format_exc())
            return f"An error occurred while analyzing {url}: {str(e)}"

    def capture_website_screenshot(self, url):
        try:
            self.logger.info(f"Attempting to capture screenshot of {url}")
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.get(url)
            
            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll to capture full page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for any lazy-loaded content
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"screenshot_{timestamp}.png"
            screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
            
            driver.save_screenshot(screenshot_path)
            driver.quit()
            return screenshot_path
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def encode_image(self, image_path):
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('ascii')
        except Exception as e:
            self.logger.error(f"Failed to encode image: {str(e)}")
            return None

    def analyze_image(self, encoded_image):
        if not encoded_image:
            return "Failed to encode image for analysis."

        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are an AI assistant that analyzes website screenshots and provides detailed descriptions."}]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}},
                        {"type": "text", "text": "Analyze this website screenshot and provide a detailed description of its content, layout, and purpose."}
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
            self.logger.error(f"Failed to analyze the image: {str(e)}")
            return f"Failed to analyze the image. Error: {str(e)}"

    def extract_content_selenium(self, url):
        try:
            self.logger.info(f"Attempting to extract content from {url} using Selenium")
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.get(url)
            
            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract text content
            content = driver.find_element(By.TAG_NAME, "body").text
            driver.quit()
            return content
        except Exception as e:
            self.logger.error(f"Failed to extract content using Selenium: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def extract_content_requests(self, url):
        try:
            self.logger.info(f"Attempting to extract content from {url} using requests")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup.get_text()
        except Exception as e:
            self.logger.error(f"Failed to extract content using requests: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def analyze_text(self, content):
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are an AI assistant that analyzes website content and provides detailed descriptions."}]
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": f"Analyze this website content and provide a summary of its main topics and purpose:\n\n{content[:4000]}"}]
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
            self.logger.error(f"Failed to analyze the text content: {str(e)}")
            return f"Failed to analyze the text content. Error: {str(e)}"