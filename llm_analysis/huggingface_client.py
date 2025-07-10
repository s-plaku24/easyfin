"""
Hugging Face API client for Qwen3-4B model
"""

import requests
import json
import time
from config import HUGGINGFACE_API_KEY, HUGGINGFACE_API_URL

class HuggingFaceClient:
    def __init__(self):
        self.api_key = HUGGINGFACE_API_KEY
        self.api_url = HUGGINGFACE_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def query_model(self, prompt, max_retries=3, retry_delay=10):
        """
        Send a query to the Hugging Face model
        
        Args:
            prompt (str): The prompt to send to the model
            max_retries (int): Maximum number of retries
            retry_delay (int): Delay between retries in seconds
        
        Returns:
            str: Model response or None if failed
        """
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 2000,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=120  # 2 minute timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Handle different response formats
                    if isinstance(result, list) and len(result) > 0:
                        if 'generated_text' in result[0]:
                            text = result[0]['generated_text']
                        else:
                            text = str(result[0])
                    elif isinstance(result, dict):
                        if 'generated_text' in result:
                            text = result['generated_text']
                        else:
                            text = str(result)
                    else:
                        text = str(result)
                    
                    return text
                
                elif response.status_code == 503:
                    # Model is loading, wait and retry
                    time.sleep(retry_delay)
                    continue
                
                else:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    continue
                    
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue
            
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue
        
        return None
    
    def test_connection(self):
        """
        Test the Hugging Face API connection
        
        Returns:
            bool: True if connection works, False otherwise
        """
        try:
            test_prompt = "Hello, this is a test. Please respond briefly."
            response = self.query_model(test_prompt, max_retries=1)
            
            if response:
                return True
            else:
                return False
                
        except Exception as e:
            return False