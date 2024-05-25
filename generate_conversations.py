"""Generates conversations from the given conversation opener."""

import concurrent.futures
import glob
import json
import os
from typing import Any

from absl import app, flags, logging

from darkgpt.models import BaseModel, Context, Message, ModelRegistry, Role

FLAGS = flags.FLAGS

flags.DEFINE_string("model", "openai", "The model to use for the simulation")
flags.DEFINE_multi_string(
    "model_arg",
    default=[],
    help="model parameter values as arg_name=arg_value",
)
flags.DEFINE_boolean(
    "ignore_response",
    False,
    "In the message history for each new chat completion, use the chatbot response from the recorded conversation and NOT the generated response",
)
flags.DEFINE_string(
    "dataset_dir",
    None,
    "Conversation dataset recorded from conversation between user and bot agent.",
)
flags.DEFINE_string(
    "output_dir", None, "Output directory to save the generated conversations."
)
flags.DEFINE_integer("limit", None, "Limit the number of conversations to generate")


def load_dataset(dataset_dir: str, limit: int | None = None):
    for idx_file, filename in enumerate(
        glob.glob(os.path.join(dataset_dir, "*.json")),
        1,
    ):
        with open(filename, "r") as f:
            entry: dict[str, Any] = json.load(f)
        yield entry

        if limit is not None and idx_file >= limit:
            break


def run_simulation(
    model: BaseModel,
    data_entry: dict[str, Any],
    ignore_response: bool = True,
):
    logging.info("Running simulation for entry %s", data_entry["id"])

    context = Context()
    sim_conversations = []
    for conv in data_entry["conversations"]:
        role = Role[conv["from"]]
        message = conv["value"]
        if role != Role.human:
            if ignore_response:
                context.messages.append(Message(role=role.value, content=message))
            continue
        sim_conversations.append(conv)
        response = model.generate_with_context(
            context=context,
            message=message,
        )
        context.messages.append(Message(role=role.value, content=message))
        sim_conversations.append(
            {
                "from": Role.gpt.name,
                "value": response,
            }
        )
        if not ignore_response:
            context.messages.append(Message(role=Role.gpt.value, content=response))

    data_entry["conversations"] = sim_conversations
    return data_entry


def main(_):
    os.makedirs(FLAGS.output_dir, exist_ok=True)
    dataset = load_dataset(FLAGS.dataset_dir, limit=FLAGS.limit)
    logging.info("Using model %s with args %s", FLAGS.model, FLAGS.model_arg)
    model = ModelRegistry.get(FLAGS.model, FLAGS.model_arg)
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {
            executor.submit(
                run_simulation, model, entry, ignore_response=FLAGS.ignore_response
            ): (entry, 1)
            for entry in dataset
        }
        while futures:
            done, _ = concurrent.futures.wait(
                futures, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in done:
                entry, num_attempts = futures.pop(future)
                try:
                    data = future.result()
                except Exception as e:
                    logging.error(
                        "Failed attempt %d for entry %s", num_attempts, entry["id"]
                    )
                    logging.error(e)
                    if num_attempts < 3:
                        futures[
                            executor.submit(
                                run_simulation,
                                model,
                                entry,
                                ignore_response=FLAGS.ignore_response,
                            )
                        ] = (
                            entry,
                            num_attempts + 1,
                        )
                    continue

                output_path = os.path.join(FLAGS.output_dir, f"{data['id']}.json")
                with open(output_path, "w") as f:
                    json.dump(data, f)

                logging.info(
                    "Saved conversation for entry %s to %s",
                    data["id"],
                    output_path,
                )


if __name__ == "__main__":
    app.run(main)
