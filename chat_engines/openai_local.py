# This version uses GPT API online
from chat_engines.IChatEngine import IChatEngine
from openai import OpenAI
import os
from collections import deque


class ChatEngine(IChatEngine):
    settings = None
    client = None

    # This is the system prompt that will be used in every interaction
    system_prompt = "The following is a conversation with an AI assistant.  The assistant is helpful, creative, clever, and very friendly."
    # And the prompts will be primed with these examples (which will scroll off as we reach history_length)
    conversation = []
    conversation.append({'role': 'system', 'content': system_prompt})
    conversation.append({'role': 'user', 'content': "Hello, how are you?"})
    conversation.append({'role': 'assistant', 'content': "How can I help you today?"})

    # Constructor that gives us our settings
    def __init__(self, settings):
        self.settings = settings
        # Get the user's OpenAI API key and base URL from the environment
        self.client = OpenAI(api_key=os.environ['OPENAI_API_KEY'], base_url=os.environ['OPENAI_BASE_URL'])

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
        self.conversation.append({'role': 'assistant', 'content': text})
        return text

