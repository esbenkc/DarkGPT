from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from typing import NamedTuple


class Role(enum.Enum):
    human = "user"
    model = "assistant"
    system = "system"


class Message(NamedTuple):
    role: str
    content: str


class Context:
    def __init__(self, messages: list[Message] | None = None):
        self.messages = messages or []

    def to_list(self) -> list[dict[str, str]]:
        return [message._asdict() for message in self.messages]

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
