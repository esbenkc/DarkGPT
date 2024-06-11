import csv
import hashlib
import json
import pathlib
import re
from collections import defaultdict

import click
import ruamel.yaml

from darkgpt.models import Role


@click.command()
@click.option(
    "--prompts-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    required=True,
    help="Path to the benchmark prompts CSV file.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, writable=True, path_type=pathlib.Path),
    required=True,
    help="Directory to save the output JSON files.",
)
def main(prompts_file: pathlib.Path, output_dir: pathlib.Path):
    manifest = defaultdict(list)
    with prompts_file.open(mode="r", newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            for prompt_type, prompt in row.items():
                prompt = prompt.strip()
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
                            "conversation": [
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
    main()
