from __future__ import annotations

from typing import Any

import jinja2

from darkgpt.models.base import BaseModel, Context, Role


class Replicate(BaseModel):
    """For messages with chat history to work, need to provide a Jinja2 chat template
    compatible with the chosen model. Messages will be passed to the template as
    the `messages` variable, with each message in the list being a dictionary
    with the keys `role` (either "user" or "assistant") and `content`.
    """

    def __init__(
        self,
        model_name: str,
        user: str | None = None,
        version: str | None = None,
        chat_template: str | None = None,
        **params: Any,
    ):
        import replicate

        self._client = replicate.Client()
        self._chat_template = (
            jinja2.Environment().from_string(chat_template) if chat_template else None
        )
        if user:
            model_name = f"{user}/{model_name}"
        model = self._client.models.get(model_name)
        if version:
            model = model.versions.get(version)
        self._model = model
        self._params = {"temperature": 0, **params}

    def generate(self, message: str, preprompt: str | None = None) -> str:
        prompt = {**self._params, "prompt": message}
        if preprompt:
            prompt["system_prompt"] = preprompt

        return "".join(self._client.run(self._model, input=prompt))

    def generate_with_context(self, context: Context, message: str) -> str:
        if len(context.messages) > 0 and self._chat_template is None:
            raise ValueError(
                "Chat template must be provided to use Replicate models with message history"
            )

        messages = context.to_list()
        messages.append({"role": Role.human.value, "content": message})
        message = self._chat_template.render(messages=messages).strip()
        return self.generate(message)
