"""Evaluates the presence of dark patterns in a conversation."""

import concurrent.futures
import glob
import json
import os

import ruamel.yaml
from absl import app, flags, logging

from darkgpt.agents import Overseer
from darkgpt.models import ModelRegistry

FLAGS = flags.FLAGS


def load_dataset_from_dir(dataset_dir: str, limit: int | None = None):
    for idx_file, filename in enumerate(
        glob.glob(os.path.join(dataset_dir, "*.json")),
        1,
    ):
        with open(filename, "r") as f:
            entry = json.load(f)
        yield entry

        if limit and idx_file >= limit:
            break


def evaluate_and_save(overseer: Overseer, entry: dict):
    logging.info("Evaluating entry %s", entry["id"])
    eval, sampled_convs = overseer.evaluate(entry)
    result = {
        "id": entry["id"],
        "dialogue": eval["dialogue"],
        "ethical_issues": {
            issue_type: bool(value)
            for issue_type, value in sorted(eval["ethical_issues"].items())
        },
        "conversations": sampled_convs,
    }
    return result


def main(_):
    yaml = ruamel.yaml.YAML(typ="safe")
    yaml.default_flow_style = False
    with open(FLAGS.params_file, "r") as file:
        model_params = yaml.load(file)["models"][FLAGS.model]
    logging.info("Using model %s with args %s", FLAGS.model, model_params)
    model = ModelRegistry.get(
        model_params.pop("type"), model_name=FLAGS.model, **model_params
    )
    overseer = Overseer(model)

    os.makedirs(FLAGS.output_dir, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        futures = {
            executor.submit(evaluate_and_save, overseer, entry): (entry, 1)
            for entry in load_dataset_from_dir(FLAGS.dataset_dir, limit=FLAGS.limit)
        }

        while futures:
            done, _ = concurrent.futures.wait(
                futures, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in done:
                entry, num_attemps = futures.pop(future)
                entry_id = entry["id"]
                try:
                    eval_result = future.result()
                except Exception as e:
                    logging.error(
                        "Failed attempt %d for entry %s: %s",
                        num_attemps,
                        entry_id,
                        e,
                    )
                    if num_attemps < 3:
                        futures[executor.submit(evaluate_and_save, overseer, entry)] = (
                            entry,
                            num_attemps + 1,
                        )
                    continue

                logging.info(
                    "Id: %s Result: %s",
                    entry_id,
                    json.dumps(eval_result["ethical_issues"], indent=4, sort_keys=True),
                )
                output_path = os.path.join(FLAGS.output_dir, f"{entry_id}.yaml")
                with open(output_path, "w") as file:
                    yaml.dump(eval_result, file)
                logging.info("Saved result to %s", output_path)


if __name__ == "__main__":
    flags.DEFINE_string(
        "model",
        None,
        "The model to use for the simulation",
        required=True,
    )
    flags.DEFINE_string(
        "params_file",
        "params.yaml",
        "file containing model parameters",
    )
    flags.DEFINE_string(
        "dataset_dir",
        None,
        "Directory of conversations between users and chatbot.",
    )
    flags.DEFINE_string(
        "output_dir",
        None,
        "Path to output directory of the overseer's evaluation results",
    )
    flags.DEFINE_integer("limit", None, "Limit the number of conversations to evaluate")

    app.run(main)
