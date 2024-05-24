import os
from abc import ABC, abstractmethod
from typing import NamedTuple

import google.generativeai as genai
from openai import OpenAI


class Message(NamedTuple):
    role: str
    message: str


class Context:
    def __init__(self, messages: list[Message] | None = None):
        self.messages = messages or []

    def to_list(self):
        return [message._asdict() for message in self.messages]

    def to_gemini_history(self):
        return [
            {
                "part": {
                    "text": message.message,
                    "inline_data": None,
                },
                "role": message.role,
            }
            for message in self.messages
        ]

    def to_string(self):
        return "\n".join(
            [f"{message.role}: {message.message}" for message in self.messages]
        )


class BaseModel(ABC):
    @abstractmethod
    def generate(self, message: str, preprompt: str | None = None) -> str:
        pass

    @abstractmethod
    def generate_with_context(self, context: Context, message: str) -> str:
        pass

    def __str__(self):
        return self.__class__.__name__


class OpenAIGpt(BaseModel):
    def __init__(self, model_name="gpt-4-turbo-preview"):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model_name = model_name

    def generate(self, message: str, preprompt: str | None = None) -> str:
        if not preprompt:
            preprompt = "You are a helpful assistant."

        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": preprompt},
                {"role": "user", "content": message},
            ],
            model=self.model_name,
            temperature=0,
        )
        return response.choices[0].message.content

    def generate_with_context(self, context: Context, message: str) -> str:
        messages = context.to_list()
        messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            messages=messages, model=self.model_name
        )
        return response.choices[0].message.content

    def __str__(self):
        return "OpenAI GPT-4"


class Gemini(BaseModel):
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-pro")

    def generate(self, message: str, preprompt: str | None = None) -> str:
        if preprompt:
            message = f"{preprompt.rstrip('.')}. \n{message}"

        response = self.model.generate_content(message)
        return response.text

    def generate_with_context(self, context: Context, message: str) -> str:
        chat_session = self.model.start_chat(history=context.to_gemini_history())
        return chat_session.send_message(message).text

    def __str__(self):
        return "Gemini"
