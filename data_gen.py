import json
import random

from absl import app, flags, logging

FLAGS = flags.FLAGS

flags.DEFINE_string(
    "dataset",
    None,
    "Dataset of conversations between users and a chatbot.",
)
flags.DEFINE_integer("size", 500, "Number of conversations to sample")
flags.DEFINE_string(
    "output_dir", None, "Path to output directory for the sampled conversations"
)
flags.DEFINE_integer(
    "max_length",
    5,
    "Maximum number of user or chatbot messages to include in each conversation",
)


def sample(
    conversations: list[dict[str, str]], max_length: int = 5
) -> list[dict[str, str]]:
    length = len(conversations)
    if length > max_length:
        begin = random.randint(0, length - max_length)
        conversations = conversations[begin : begin + max_length]

    return conversations


def main(_):
    with open(FLAGS.dataset, "r") as f:
        dataset = json.load(f)
    dataset = dataset[: FLAGS.size]
    for entry in dataset:
        entry["conversations"] = sample(
            entry["conversations"], max_length=FLAGS.max_length
        )
        with open(f"{FLAGS.output_dir}/{entry['id']}.json", "w") as f:
            json.dump(entry, f, indent=4)
        logging.info("Wrote entry %s to %s", entry["id"], f.name)


if __name__ == "__main__":
    app.run(main)
