"""Driver app for the simulation."""

import concurrent.futures
import glob
import json
import os

import google.generativeai as genai
from absl import app, flags, logging

from darkgpt.agents import Overseer
from darkgpt.models import Gemini, OpenAIGpt

FLAGS = flags.FLAGS

flags.DEFINE_string("model", "openai", "The model to use for the simulation")
flags.DEFINE_multi_string(
    "model_arg",
    default=[],
    help="model parameter values as arg_name=arg_value",
)
flags.DEFINE_string(
    "dataset_dir",
    None,
    "Conversation dataset recorded from conversation between user and bot agent.",
)
flags.DEFINE_string(
    "output_dir", None, "Path to output directory of the overseer's evaluation results"
)


MODEL_MAP = {
    "openai": (OpenAIGpt, {"model_name": "gpt-4-0125-preview"}),
    "gemini": (Gemini, {}),
}


def _get_model(model_name: str):
    if model_name not in MODEL_MAP:
        raise ValueError(f"Model {model_name} not found")

    Model, default_args = MODEL_MAP[model_name]
    model_args = {**default_args}
    for model_arg in FLAGS.model_arg:
        param_name, _, param_value = model_arg.partition("=")
        model_args[param_name] = param_value

    logging.info("Using model: %s with args: %s", model_name, model_args)

    return Model(**model_args)


def load_dataset(dataset_path: str):
    with open(dataset_path, "r") as f:
        dataset = json.load(f)
    yield from dataset


def load_dataset_from_dir(dataset_dir: str):
    for filename in glob.glob(os.path.join(dataset_dir, "*.json")):
        with open(filename, "r") as f:
            entry = json.load(f)
        yield entry


def evaluate_and_save(overseer: Overseer, entry: dict):
    logging.info("Evaluating entry %s", entry["id"])
    result, sampled_convs = overseer.evaluate(entry, max_tries=3)
    result["id"] = entry["id"]
    result["conversations"] = sampled_convs
    return result


def main(_):
    model = _get_model(FLAGS.model)
    overseer = Overseer(model)
    os.makedirs(FLAGS.output_dir, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        futures = []
        for entry in load_dataset_from_dir(FLAGS.dataset_dir):
            future = executor.submit(evaluate_and_save, overseer, entry)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            try:
                eval_result = future.result()
            except Exception as e:
                logging.error("Error evaluating entry: %s", e)
                continue

            logging.info(
                "Id: %s Result: %s",
                json.dumps(eval_result["ethical_issues"], indent=4),
                eval_result,
            )
            output_path = os.path.join(FLAGS.output_dir, eval_result["id"] + ".json")
            with open(output_path, "w") as f:
                json.dump(eval_result, f)
                logging.info("Saved result to %s", output_path)


if __name__ == "__main__":
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=GOOGLE_API_KEY)

    app.run(main)
