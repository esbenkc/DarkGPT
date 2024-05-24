import json
import random

from absl import app, flags, logging

FLAGS = flags.FLAGS

flags.DEFINE_string(
    "dataset",
    None,
    "Conversation dataset recorded from conversation between user and bot agent.",
)
flags.DEFINE_string(
    "output_dir", None, "Path to output directory of the overseer's evaluation results"
)
flags.DEFINE_integer("max_length", 5, "Maximum length of conversation to sample")
flags.DEFINE_integer("size", 500, "Number of entries to sample")


def sample(conversations, max_length=5):
    length = len(conversations)
    if length > max_length:
        begin = random.randint(0, length - max_length)
        convs = conversations[begin : begin + max_length]
    else:
        convs = conversations

    return convs


def main(_):
    with open(FLAGS.dataset, "r") as f:
        dataset = json.load(f)
        dataset = dataset[: FLAGS.size]
        for entry in dataset:
            entry["conversations"] = sample(entry["conversations"], FLAGS.max_length)
            with open(f"{FLAGS.output_dir}/{entry['id']}.json", "w") as f:
                json.dump(entry, f, indent=4)
                logging.info("Wrote entry %s to %s", entry["id"], f.name)


if __name__ == "__main__":
    app.run(main)
