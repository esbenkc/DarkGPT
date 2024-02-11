"""Driver app for the simulation."""
import os

from absl import app
from absl import flags
from absl import logging
from dotenv import load_dotenv

from models import Gemini, OpenAIGpt4


load_dotenv()

print(os.environ)


FLAGS = flags.FLAGS


def main(_):
    logging.info('starting simultation...')
    sessions = [OpenAIGpt4(), Gemini()]

    for session in sessions:
        message = 'Hello'
        response = session.generate(message)
        print(response)


if __name__ == '__main__':
    app.run(main)
