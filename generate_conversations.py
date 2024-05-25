"""Generates conversations from the given conversation opener."""

import concurrent.futures
import glob
import json
import os

import google.generativeai as genai
from absl import app, flags, logging
from dotenv import load_dotenv
from openai import OpenAI

FLAGS = flags.FLAGS

flags.DEFINE_string(
    "model_name", "gpt-3.5-turbo", "The openai model name to use for the simulation"
)
flags.DEFINE_string(
    "dataset_dir",
    None,
    "Conversation dataset recorded from conversation between user and bot agent.",
)
flags.DEFINE_string(
    "output_dir", None, "Output directory to save the generated conversations."
)


def load_dataset(dataset_dir):
    for filename in glob.glob(os.path.join(dataset_dir, "*.json")):
        with open(filename, "r") as f:
            entry = json.load(f)
            yield entry


def get_role(from_):
    if from_ == "human":
        return "user"
    if from_ == "gpt":
        return "assistant"
    if from_ == "system":
        return "system"

    raise ValueError(f"Unknown role {from_}")


def run_simulation(data_entry):
    logging.info("Running simulation for entry %s", data_entry["id"])
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    messages = []
    sim_conversations = []
    for conv in data_entry["conversations"]:
        if conv["from"] == "human":
            sim_conversations.append(conv)
            messages.append({"content": conv["value"], "role": get_role(conv["from"])})
            response = client.chat.completions.create(
                messages=messages, model=FLAGS.model_name
            )
            sim_conversations.append(
                {"from": "gpt", "value": response.choices[0].message.content}
            )

    data_entry["conversations"] = sim_conversations
    return data_entry


def main(_):
    os.makedirs(FLAGS.output_dir, exist_ok=True)
    dataset = load_dataset(FLAGS.dataset_dir)
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for entry in dataset:
            futures.append(executor.submit(run_simulation, entry))

        for future in concurrent.futures.as_completed(futures):
            data = future.result()
            output_path = os.path.join(FLAGS.output_dir, f"{data['id']}.json")
            with open(output_path, "w") as f:
                json.dump(data, f)
            logging.info(
                "Saved conversation for entry %s to %s", data["id"], output_path
            )


if __name__ == "__main__":
    load_dotenv()

    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=GOOGLE_API_KEY)

    app.run(main)
