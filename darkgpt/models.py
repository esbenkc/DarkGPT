import enum
from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import NamedTuple

import anthropic
import google.generativeai as genai
from openai import OpenAI


class Role(enum.Enum):
    human = "user"
    gpt = "assistant"
    system = "system"


class Message(NamedTuple):
    role: str
    content: str


class Context:
    def __init__(self, messages: list[Message] | None = None):
        self.messages = messages or []

    def to_list(self):
        return [message._asdict() for message in self.messages]

    def to_gemini_history(self):
        return [
            {
                "part": {
                    "text": message.content,
                    "inline_data": None,
                },
                "role": message.role,
            }
            for message in self.messages
        ]

    def to_string(self):
        return "\n".join(
            [f"{message.role}: {message.content}" for message in self.messages]
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
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        self._client = OpenAI()
        self._model_name = model_name

    def _generate(self, messages: list[dict[str, str]]) -> str:
        response = self._client.chat.completions.create(
            messages=messages,
            model=self._model_name,
            temperature=0,
        )
        return response.choices[0].message.content

    def generate(self, message: str, preprompt: str | None = None) -> str:
        if not preprompt:
            preprompt = "You are a helpful assistant."

        return self._generate(
            [
                {"role": Role.system.value, "content": preprompt},
                {"role": Role.human.value, "content": message},
            ]
        )

    def generate_with_context(self, context: Context, message: str) -> str:
        messages = context.to_list()
        messages.append({"role": Role.human.value, "content": message})
        return self._generate(messages)

    def __str__(self):
        return f"OpenAI GPT ({self._model_name})"


class Gemini(BaseModel):
    def __init__(self, model_name: str = "gemini-pro"):
        self._model = genai.GenerativeModel(model_name)
        self._model_name = model_name

    def generate(self, message: str, preprompt: str | None = None) -> str:
        if preprompt:
            message = f"{preprompt.rstrip('.')}. \n{message}"

        response = self._model.generate_content(message)
        return response.text

    def generate_with_context(self, context: Context, message: str) -> str:
        chat_session = self._model.start_chat(history=context.to_gemini_history())
        return chat_session.send_message(message).text

    def __str__(self):
        return f"Gemini ({self._model_name})"


class Claude(BaseModel):
    def __init__(
        self,
        model_name: str = "claude-3-sonnet-20240229",
        max_tokens: int = 1024,
    ):
        self._client = anthropic.Anthropic()
        self._model_name = model_name
        self._max_tokens = max_tokens

    def _generate(self, messages: list[dict[str, str]]) -> str:
        response = self._client.messages.create(
            max_tokens=self._max_tokens,
            messages=messages,
            model=self._model_name,
        )
        return response.content[0].text

    def generate(self, message: str, preprompt: str | None = None) -> str:
        if preprompt:
            message = f"{preprompt.rstrip('.')}. \n{message}"
        return self._generate([{"role": Role.human.value, "content": message}])

    def generate_with_context(self, context: Context, message: str) -> str:
        messages = context.to_list()
        messages.append({"role": Role.human.value, "content": message})
        return self._generate(messages)

    def __str__(self):
        return f"Claude ({self._model_name})"


class ModelRegistry:
    _REGISTRY = MappingProxyType(
        {
            "claude": Claude,
            "gemini": Gemini,
            "openai": OpenAIGpt,
        }
    )

    @classmethod
    def get(cls, model_type: str, args: list[str]):
        Model = cls._REGISTRY.get(model_type, None)
        if Model is None:
            raise ValueError(f"Model {model_type} not found")

        model_args = {}
        for model_arg in args:
            param_name, _, param_value = model_arg.partition("=")
            model_args[param_name] = param_value

        return Model(**model_args)
