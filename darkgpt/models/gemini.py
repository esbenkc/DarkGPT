from __future__ import annotations

from typing import Any

from darkgpt.models.base import BaseModel, Context, Role


class Gemini(BaseModel):
    def __init__(self, model_name: str = "gemini-pro", **generation_config: Any):
        import google.generativeai as genai
        import google.generativeai.types as genai_types

        self._model = genai.GenerativeModel(model_name)
        self._model_name = model_name
        self._generation_config = {"temperature": 0, **generation_config}
        self._safety_setting = {
            harm_category: genai_types.HarmBlockThreshold.BLOCK_NONE
            for harm_category in genai_types.HarmCategory
            if harm_category != genai_types.HarmCategory.HARM_CATEGORY_UNSPECIFIED
        }

    @classmethod
    def convert_context(cls, context: Context):
        return [
            {
                "parts": [{"text": message.content}],
                "role": "model" if Role(message.role) == Role.model else message.role,
            }
            for message in context.messages
        ]

    def generate(self, message: str, preprompt: str | None = None) -> str:
        if preprompt:
            message = f"{preprompt.rstrip('.')}. \n{message}"

        response = self._model.generate_content(
            message,
            generation_config=self._generation_config,
            safety_settings=self._safety_setting,
        )
        return response.text.strip()

    def generate_with_context(self, context: Context, message: str) -> str:
        chat_session = self._model.start_chat(history=self.convert_context(context))
        return chat_session.send_message(
            message,
            generation_config=self._generation_config,
            safety_settings=self._safety_setting,
        ).text.strip()

    def __str__(self):
        return f"Gemini ({self._model_name})"
