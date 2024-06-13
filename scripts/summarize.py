from __future__ import annotations

import pathlib
from collections import defaultdict

import click
import ruamel.yaml


@click.command()
@click.option(
    "--evals-dir",
    type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path),
    help="Directory containing eval files",
    required=True,
)
@click.option(
    "--output-file",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    help="Output YAML file name",
    required=True,
)
@click.option(
    "--manifest",
    type=(click.Path(exists=True, dir_okay=False, path_type=pathlib.Path), str),
    help="Prompt manifest file and category",
    required=True,
)
@click.option(
    "--params-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    help="Params file",
    default="params.yaml",
)
def main(
    evals_dir: pathlib.Path,
    output_file: pathlib.Path,
    manifest: tuple[pathlib.Path, str],
    params_file: pathlib.Path,
):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    yaml = ruamel.yaml.YAML(typ="safe")
    yaml.default_flow_style = False
    manifest_file, category = manifest
    with open(manifest_file, "r") as file:
        prompt_ids: list[str] = yaml.load(file)[category]

    with open(params_file, "r") as file:
        overseers: list[str] = yaml.load(file)["eval"]["overseers"]

    metrics = defaultdict(lambda: defaultdict(int))
    for prompt_id in prompt_ids:
        for overseer in overseers:
            eval_file = f"{evals_dir}/{overseer}/{prompt_id}.yaml"
            with open(eval_file, "r") as file:
                content: dict[str, bool] = yaml.load(file)

            if (ethical_issues := content.get("ethical_issues", None)) is None:
                continue

            for key, value in ethical_issues.items():
                metrics[key][overseer] += value

    averages = {
        key: {overseer: count for overseer, count in sorted(values.items())}
        for key, values in sorted(metrics.items())
    }

    with open(output_file, "w") as file:
        yaml.dump(averages, file)


if __name__ == "__main__":
    main()
