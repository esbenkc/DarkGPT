from __future__ import annotations

import hashlib
import json
import pathlib
from typing import TYPE_CHECKING, Any

import click
import dominate.tags
import jinja2
import numpy as np
import ruamel.yaml

if TYPE_CHECKING:
    from numpy.typing import NDArray


def sample_prompts(prompts: dict[str, list[str]], models: list[str]):
    model_hashes = [hashlib.sha256(model.encode()).hexdigest() for model in models]
    models, model_hashes = zip(
        *[
            (models[idx_hash], model_hashes[idx_hash])
            for idx_hash in np.argsort(model_hashes)
        ]
    )

    sampled_prompts: dict[str, list[tuple[str, str]]] = {}
    for category, category_prompts in prompts.items():
        category_prompts = sorted(category_prompts)
        prompt_assignments: NDArray[np.int_] = np.searchsorted(
            category_prompts, model_hashes
        )
        for idx_model, idx_prompt in enumerate(prompt_assignments[1:], 1):
            previous_assignment = prompt_assignments[idx_model - 1]
            if idx_prompt <= previous_assignment:
                prompt_assignments[idx_model] = previous_assignment + 1

        prompt_assignments[-1] = min(prompt_assignments[-1], len(category_prompts) - 1)
        for idx_model, idx_prompt in reversed(list(enumerate(prompt_assignments[:-1]))):
            next_assignment = prompt_assignments[idx_model + 1]
            if idx_prompt >= next_assignment:
                prompt_assignments[idx_model] = next_assignment - 1

        assert sorted(prompt_assignments) == prompt_assignments.tolist()
        assert len(set(prompt_assignments)) == len(prompt_assignments)
        assert prompt_assignments[0] >= 0
        assert prompt_assignments[-1] < len(category_prompts)

        sampled_prompts[category] = [
            (model, category_prompts[idx_prompt])
            for model, idx_prompt in zip(models, prompt_assignments)
        ]

    return sampled_prompts


@click.command()
@click.option(
    "--conversations-dir",
    type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path),
    required=True,
    help="The directory to generated conversations",
)
@click.option(
    "--prompt-manifest-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    required=True,
    help="Manifest file of categories and prompts",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, writable=True, path_type=pathlib.Path),
    required=True,
    help="The path to the output directory.",
)
@click.option(
    "--params-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    default="params.yaml",
    help="The path to the parameters file.",
)
@click.option(
    "--template-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    default="template.lsq",
    help="The path to the template file.",
)
def main(
    conversations_dir: pathlib.Path,
    prompt_manifest_file: pathlib.Path,
    output_dir: pathlib.Path,
    params_file: pathlib.Path,
    template_file: str,
):
    """Sample a unique prompt from each category for each model and generate
    a .lsq file for each."""
    yaml = ruamel.yaml.YAML(typ="safe")
    with open(prompt_manifest_file, "r") as file:
        prompts: dict[str, list[str]] = yaml.load(file)

    with open(template_file, "r") as file:
        template = jinja2.Template(file.read())

    with open(params_file, "r") as file:
        params: dict[str, Any] = ruamel.yaml.YAML(typ="safe").load(file)
    models: list[str] = params["assistants"]
    params = params["sample"]

    sampled_prompts = sample_prompts(prompts, models)

    for category, category_prompts in sampled_prompts.items():
        for model, prompt_id in category_prompts:
            conversation_file = (
                conversations_dir / model / category / f"{prompt_id}.json"
            )
            with conversation_file.open("r") as file:
                prompt, output = (
                    message["value"] for message in json.load(file)["conversation"]
                )

            conversation_html = "\n".join(
                [
                    dominate.tags.p(
                        dominate.tags.strong(f"{label}:"), " ", text
                    ).render()
                    for label, text in [
                        ("Human", prompt),
                        ("AI model", output),
                    ]
                ]
            )

            output_file = output_dir / model / f"{category}.lsq"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(
                template.render(
                    conversation_html=conversation_html,
                    **params["template"],
                )
            )

    click.echo(f"Processing completed. Generated files are in the folder: {output_dir}")


if __name__ == "__main__":
    main()
