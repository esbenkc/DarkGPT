import csv
import hashlib
import json
import pathlib
import re
from collections import defaultdict

import ruamel.yaml
from absl import app, flags

from darkgpt.models import Role

FLAGS = flags.FLAGS


def main(_):
    dataset_path = pathlib.Path(FLAGS.dataset)
    output_dir = pathlib.Path(FLAGS.output_dir)

    manifest = defaultdict(list)
    with open(dataset_path, mode="r", newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            for prompt_type, prompt in row.items():
                if not prompt:
                    continue

                prompt_id = hashlib.sha256(prompt.encode()).hexdigest()
                category = re.sub(
                    r"[^a-z]+", "_", prompt_type, flags=re.IGNORECASE
                ).lower()
                prompt_file = output_dir / category / f"{prompt_id}.json"
                prompt_file.parent.mkdir(parents=True, exist_ok=True)

                manifest[category].append(prompt_id)
                with open(prompt_file, "w", encoding="utf-8") as file:
                    json.dump(
                        {
                            "id": prompt_id,
                            "conversations": [
                                {
                                    "from": Role.human.name,
                                    "value": prompt,
                                }
                            ],
                        },
                        file,
                        sort_keys=True,
                    )

    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    with (output_dir / "manifest.yaml").open("w") as file:
        yaml.dump(
            {category: sorted(files) for category, files in sorted(manifest.items())},
            file,
        )


if __name__ == "__main__":
    flags.DEFINE_string("dataset", None, "Path to the dataset CSV file.")
    flags.DEFINE_string("output_dir", None, "Directory to save the output JSON files.")
    app.run(main)
