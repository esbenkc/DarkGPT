"""Driver app for the simulation."""
import os

from absl import app
from absl import flags
from absl import logging
from dotenv import load_dotenv
import google.generativeai as genai

from models import Gemini, OpenAIGpt4, BaseModel
from agents import HumanAgent, Overseer, BaseAgent

load_dotenv()

FLAGS = flags.FLAGS

flags.DEFINE_string("model", "openai", "The model to use for the simulation")
flags.DEFINE_string("message", "What is the meaning of life?", "The message to send to the model")
flags.DEFINE_string("criteria", "Is the answer helpful?", "The criteria to use for judging the response.")


GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


MODEL_MAP = {
    "openai": OpenAIGpt4(),
    "gemini": Gemini()
}


def _get_model(model_name):
    return MODEL_MAP.get(model_name, None)


def simulate_dialogue(user: BaseAgent, bot: BaseAgent, first_message: str, max_length=10):
    resp = user.generate(first_message)
    count = 0
    while count < max_length:
        pass


def main(_):
    model = _get_model()

    if model is None:
        logging.error(f"Model {FLAGS.model} not found")
        return
    else:
        logging.info(f"Using model {model}")

    response = model.generate('What is the meaning of life?')
    logging.info(response.text)




if __name__ == '__main__':
    app.run(main)
