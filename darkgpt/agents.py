import json
import pathlib
from abc import ABC, abstractmethod
from typing import Any, Mapping, Sequence

import jinja2
from absl import logging

import darkgpt
from darkgpt.models import BaseModel, Context, Message

_PROMPTS_DIR = pathlib.Path(darkgpt.__file__).parent / "prompts"


class BaseAgent(ABC):
    def __init__(self, model: BaseModel, role: str):
        self.model = model
        self.role = role
        self.context = Context()

    def set_context(self, context: Context):
        self.context = context

    def _add_message_to_context(self, message: str):
        self.context.messages.append(Message(role="user", content=message))

    @abstractmethod
    def chat(self, message: Message) -> str:
        pass


class LLMAgent(BaseAgent):
    def chat(self, message: str) -> str:
        resp = self.model.generate_with_context(self.context, message)
        self._add_message_to_context(resp)
        return resp


class Overseer(LLMAgent):
    def __init__(self, model: BaseModel):
        role = (_PROMPTS_DIR / "overseer/system.md").read_text()
        super().__init__(model, role)

    @classmethod
    def make_prompt(cls, conversations: Sequence[Mapping[str, Any]]):
        template = jinja2.Environment(
            loader=jinja2.FileSystemLoader(_PROMPTS_DIR)
        ).get_template("overseer/instructions.md")
        return template.render(conversations=conversations)

    def evaluate(
        self,
        entry: dict[str, Any],
        conversations: Sequence[Mapping[str, Any]] | None = None,
    ):
        prompt = self.make_prompt(entry["conversations"])
        logging.info("Prompt: %s (length:%d)", prompt, len(prompt))
        response = self.model.generate(prompt, preprompt=self.role)

        try:
            eval_result = json.loads(response)
        except json.JSONDecodeError:
            _, split, response = response.partition("{")
            response = split + response
            response, split, _ = response.rpartition("}")
            response += split
            eval_result = json.loads(response)

        return eval_result, conversations
