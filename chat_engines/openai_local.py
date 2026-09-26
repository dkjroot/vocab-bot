# This version uses an OpenAI-compatible API (e.g. OpenAI, llama.cpp, etc.)
from chat_engines.IChatEngine import IChatEngine
from openai import OpenAI
import os
from collections import deque
import logging

class ChatEngine(IChatEngine):
    settings = None
    client = None
    conversation = []


    # Constructor that gives us our settings
    def __init__(self, settings, system_prompt):
        self.settings = settings
        # Get the OpenAI API key and base URL from the environment, with sensible defaults
        self.client = OpenAI(
            api_key=os.environ.get('OPENAI_API_KEY', 'not-needed'),
            base_url=os.environ.get('OPENAI_BASE_URL', 'http://localhost:8081/v1')
        )
        self.conversation = []
        self.conversation.append({'role': 'system', 'content': system_prompt})


    def clear_conversation(self, system_prompt):
        self.conversation = []
        self.conversation.append({'role': 'system', 'content': system_prompt})


    # Get a response from the GPT API
    def get_response(self, user_text):
        self.conversation.append({'role': 'user', 'content': user_text})
        completion = self.client.chat.completions.create(
            model=self.settings['model'],
            messages=self.conversation,
            temperature=self.settings['temperature'],
            max_tokens=self.settings['max_tokens'],
            top_p=self.settings['top_p'],
            frequency_penalty=self.settings['frequency_penalty'],
            presence_penalty=self.settings['presence_penalty'],
        )
        text = completion.choices[0].message.content.strip()
        
        # logging.getLogger(__name__).info(f"LLM Raw Response: {completion}")        
        self.conversation.append({'role': 'assistant', 'content': text})
        return text

