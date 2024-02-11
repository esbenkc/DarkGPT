import os
from typing import List

from absl import logging
from openai import OpenAI
import google.generativeai as genai


class Message:
    role: str
    message: str

    def __dict__(self):
        return {
            "role": self.role,
            "message": self.message
        }


class Context:
    messages: List[Message]

    def to_list(self):
        return [dict(message) for message in self.messages]

    def to_gemini_history(self):
        return [{
            "part": {
                "text": message.message,
                "inline_data": None,
            },
            "role": message.role
        } for message in self.messages]


class BaseModel:
    def generate(self, message, preprompt=None) -> str:
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__


class OpenAIGpt4(BaseModel):
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate(self, message, preprompt=None) -> str:
        if not preprompt:
            preprompt = "You are a helpful assistant."

        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": preprompt
                },
                {
                    "role": "user",
                    "content": message
                }],
            model="gpt-4",
            temperature=0,
        )
        return response.choices[0].message.content

    def generate_with_context(self, context: Context, message) -> str:
        messages = context.to_list()
        messages.append({
            "role": "user",
            "content": message
        })

        response = self.client.chat.completions.create(
            messages=messages,
            model="gpt-4-turbo-preview")
        return response.choices[0].message.content


    def __str__(self):
        return "OpenAI GPT-4"


class Gemini(BaseModel):
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')

    def generate(self, message, preprompt=None) ->str:
        if preprompt:
            message = f"{preprompt}. \n{message}"

        response = self.model.generate_content(message)
        return response.text

    def generate_with_context(self, context: Context, message) -> str:
        chat_session = self.model.start_chat(history=context.to_gemini_history())
        return chat_session.send_message(message).text

    def __str__(self):
        return "Gemini"
