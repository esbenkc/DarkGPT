from types import MappingProxyType
from typing import Any

from darkgpt.models.base import Context, Message, Role
from darkgpt.models.claude import Claude
from darkgpt.models.gemini import Gemini
from darkgpt.models.openai import OpenAIGpt
from darkgpt.models.replicate import Replicate


class ModelRegistry:
    _REGISTRY = MappingProxyType(
        {
            "claude": Claude,
            "gemini": Gemini,
            "openai": OpenAIGpt,
            "replicate": Replicate,
        }
    )

    @classmethod
    def get(cls, model_type: str, **kwargs: Any):
        Model = cls._REGISTRY.get(model_type, None)
        if Model is None:
            raise ValueError(f"Model {model_type} not found")

        return Model(**kwargs)


__all__ = [
    "Claude",
    "Context",
    "Gemini",
    "Message",
    "ModelRegistry",
    "OpenAIGpt",
    "Replicate",
    "Role",
]
