from __future__ import annotations

import json
import logging
import pathlib
import re
from abc import ABC, abstractmethod
from typing import Any

import jinja2

import darkgpt
from darkgpt.models.base import BaseModel, Context, Message, Role

_PROMPTS_DIR = pathlib.Path(darkgpt.__file__).parent / "prompts"

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(self, model: BaseModel, role: str):
        self.model = model
        self.role = role
        self.context = Context()

    def set_context(self, context: Context):
        self.context = context

    def _add_message_to_context(self, message: str):
        self.context.messages.append(Message(role=Role.human.value, content=message))

    @abstractmethod
    def chat(self, message: Message) -> str:
        pass


class LLMAgent(BaseAgent):
    def chat(self, message: str) -> str:
        response = self.model.generate_with_context(self.context, message)
        self._add_message_to_context(response)
        return response


class Overseer(LLMAgent):
    def __init__(
        self,
        model: BaseModel,
        issues: dict[str, dict[str, str]],
        template_globals: dict[str, Any] | None = None,
    ):
        role = (_PROMPTS_DIR / "overseer/system.md").read_text()
        super().__init__(model, role)
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(_PROMPTS_DIR))
        if template_globals:
            jinja_env.globals.update(template_globals)
        self._instructions_template = jinja_env.get_template(
            "overseer/instructions.jinja",
            globals={
                "issues": {
                    issue_name: {
                        param_name: jinja_env.from_string(param_value).render()
                        for param_name, param_value in issue_params.items()
                    }
                    for issue_name, issue_params in issues.items()
                }
            },
        )
        self._conversation_template = jinja_env.get_template("conversation.jinja")

    def make_prompt(self, conversation: str, **prompt_variables: str):
        return self._instructions_template.render(
            conversation=conversation, **prompt_variables
        )

    def evaluate(self, entry: dict[str, Any], **prompt_variables: str):
        conversation = self._conversation_template.render(
            conversation=entry["conversation"]
        )
        prompt = self.make_prompt(conversation, **(prompt_variables or {}))
        logger.info("Prompt: %s (length:%d)", prompt, len(prompt))
        response = self.model.generate(prompt, preprompt=self.role)

        try:
            eval = json.loads(response)
        except json.JSONDecodeError:
            try:
                response = re.search(r"{.+}", response, re.DOTALL).group(0)
                eval = json.loads(response)
            except Exception:
                logger.error("Failed to parse response: %s", response)
                raise

        return eval, conversation
