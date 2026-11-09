"""Google AI Studio's hosted Gemini API."""

import json
import os

from google import genai
from google.genai import errors, types

from chat_engines.IChatEngine import IChatEngine


class ChatEngine(IChatEngine):
    def __init__(self, settings, system_prompt):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Set GEMINI_API_KEY to your Google AI Studio API key.")
        self.client = genai.Client(
            api_key=api_key,
            vertexai=False,
            http_options=types.HttpOptions(timeout=60_000),
        )
        self.model = settings["model"]
        self.config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=settings.get("temperature"),
            max_output_tokens=settings.get("max_tokens"),
            top_p=settings.get("top_p"),
        )

    def clear_conversation(self, system_prompt):
        self.config.system_instruction = system_prompt

    def get_response(self, user_text):
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_text,
                config=self.config,
            )
        except errors.APIError as error:
            raise RuntimeError(
                f"Gemini returned {error.code} ({error.status}) for model {self.model}."
            ) from None

        result = (response.text or "").strip()
        try:
            json.loads(result)
        except json.JSONDecodeError:
            raise RuntimeError("Gemini did not return a complete JSON reply.") from None
        return result
