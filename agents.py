from models import Context, Message


class BaseAgent:

    def __init__(self, model, role):
        self.model = model
        self.role = role
        self.context = Context()


    def _add_message_to_context(self, message):
        self.context.append(Message(
            role="user",
            message=message
        ))
        pass

    def chat(self, context: Context, message) -> str:
        pass


class Overseer(BaseAgent):

    def __init__(self, model):
        role = """
        You are an overseer, monitoring the conversation between the human and the AI.
        """
        super().__init__(model, role)

    def chat(self, message):
        resp = self.model.generate_with_context(message, self.role)
        self._add_message_to_context(resp)
        return resp


class HumanAgent(BaseAgent):

    def __init__(self, model):
        role = """
        You are a human asking a question that may seem trivial to AI chatbots.
        """
        super().__init__(model, role)

    def chat(self, message):
        resp = self.model.generate_with_context(message, self.role)
        self._add_message_to_context(resp)
        return resp
