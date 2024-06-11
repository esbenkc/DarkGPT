from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

from darkgpt.models.base import BaseModel, Context, Role

if TYPE_CHECKING:
    from anthropic.types import MessageParam as AnthropicMessageParam


class Claude(BaseModel):
    def __init__(
        self,
        model_name: str = "claude-3-sonnet-20240229",
        max_tokens: int = 1024,
        **params: Any,
    ):
        import anthropic

        self._client = anthropic.Anthropic()
        self._model_name = model_name
        self._max_tokens = max_tokens
        self._params: dict[str, Any] = {"temperature": 0, **params}

    def _generate(self, messages: Sequence[AnthropicMessageParam]) -> str:
        response = self._client.messages.create(
            max_tokens=self._max_tokens,
            messages=messages,
            model=self._model_name,
            **self._params,
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
