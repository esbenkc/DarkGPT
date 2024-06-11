from darkgpt.models.base import BaseModel, Context, Role


class OpenAIGpt(BaseModel):
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        import openai

        self._client = openai.OpenAI()
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
