"""Evaluates the presence of dark patterns in a conversation."""

import concurrent.futures
import glob
import json
import os

import google.generativeai as genai
from absl import app, flags, logging

from darkgpt.agents import Overseer
from darkgpt.models import ModelRegistry

FLAGS = flags.FLAGS

flags.DEFINE_string("model", "openai", "The model to use as the overseer")
flags.DEFINE_multi_string(
    "model_arg",
    default=[],
    help="model parameter values as arg_name=arg_value",
)
flags.DEFINE_string(
    "dataset_dir",
    None,
    "Directory of conversations between users and chatbot.",
)
flags.DEFINE_string(
    "output_dir", None, "Path to output directory of the overseer's evaluation results"
)
flags.DEFINE_integer("limit", None, "Limit the number of conversations to evaluate")


def load_dataset_from_dir(dataset_dir: str, limit: int | None = None):
    for idx_file, filename in enumerate(
        glob.glob(os.path.join(dataset_dir, "*.json")),
        1,
    ):
        with open(filename, "r") as f:
            entry = json.load(f)
        yield entry

        if limit is not None and idx_file >= limit:
            break


def evaluate_and_save(overseer: Overseer, entry: dict):
    logging.info("Evaluating entry %s", entry["id"])
    result, sampled_convs = overseer.evaluate(entry, max_tries=3)
    result["id"] = entry["id"]
    result["conversations"] = sampled_convs
    return result


def main(_):
    logging.info("Using model %s with args %s", FLAGS.model, FLAGS.model_arg)
    model = ModelRegistry.get(FLAGS.model, FLAGS.model_arg)
    overseer = Overseer(model)
    os.makedirs(FLAGS.output_dir, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        futures = []
        for entry in load_dataset_from_dir(FLAGS.dataset_dir, limit=FLAGS.limit):
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
