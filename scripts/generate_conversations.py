from __future__ import annotations

import concurrent.futures
import json
import logging
import pathlib
from typing import TYPE_CHECKING, Any

import click
import ruamel.yaml
import tqdm

from darkgpt.models import Context, Message, ModelRegistry, Role

if TYPE_CHECKING:
    from darkgpt.models.base import BaseModel

logger = logging.getLogger(__name__)


def load_dataset(dataset_dir: pathlib.Path, limit: int | None = None):
    for idx_file, filename in enumerate(
        dataset_dir.glob("*.json"),
        1,
    ):
        with open(filename, "r") as file:
            entry: dict[str, Any] = json.load(file)
        yield entry

        if limit and idx_file >= limit:
            break


def run_simulation(
    model: BaseModel,
    entry: dict[str, Any],
    ignore_response: bool = True,
):
    logger.info("Running simulation for entry %s", entry["id"])

    context = Context()
    conversation = []
    for message in entry["conversation"]:
        role = Role[message["from"]]
        message = message["value"]
        if role != Role.human:
            if ignore_response:
                context.messages.append(Message(role=role.value, content=message))
            continue
        conversation.append(message)
        response = model.generate_with_context(
            context=context,
            message=message,
        )
        context.messages.append(Message(role=role.value, content=message))
        conversation.append(
            {
                "from": Role.model.name,
                "value": response,
            }
        )
        if not ignore_response:
            context.messages.append(Message(role=Role.model.value, content=response))

    return conversation


@click.command()
@click.option(
    "--model", "model_name", required=True, help="The model to use for the simulation"
)
@click.option(
    "--params-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    show_default=True,
    help="File containing model parameters",
    default="params.yaml",
)
@click.option(
    "--ignore-response",
    is_flag=True,
    default=False,
    help="In the message history for each new chat completion, use the chatbot response from the recorded conversation and NOT the generated response",
)
@click.option(
    "--prompts-dir",
    type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path),
    required=True,
    help="Directory of dark pattern prompts",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    required=True,
    help="Output directory to save the generated conversations.",
)
@click.option(
    "--limit",
    type=int,
    help="Limit the number of conversations to generate",
)
@click.option("--max-workers", type=int, default=50)
def main(
    model_name: str,
    prompts_dir: pathlib.Path,
    output_dir: pathlib.Path,
    params_file: pathlib.Path,
    ignore_response: bool,
    limit: int | None,
    max_workers: int,
):
    """Generates conversations from the given conversation opener."""

    yaml = ruamel.yaml.YAML(typ="safe")
    with open(params_file, "r") as file:
        model_params: dict[str, Any] = yaml.load(file)["models"][model_name]["build"]

    model_name = model_params.pop("model_name", model_name)
    model_type = model_params.pop("type")
    logger.info("Using %s model %s with args %s", model_type, model_name, model_params)

    def _get_model(**params: Any):
        return ModelRegistry.get(
            model_type,
            model_name=model_name,
            **{**model_params, **params},
        )

    model = _get_model()
    dataset = load_dataset(prompts_dir, limit=limit)

    with (
        concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor,
        tqdm.tqdm() as progress,
    ):
        futures = {
            executor.submit(
                run_simulation, model, entry, ignore_response=ignore_response
            ): (entry, 1, model)
            for entry in dataset
        }
        while futures:
            done, _ = concurrent.futures.wait(
                futures, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in done:
                entry, num_attempts, model_entry = futures.pop(future)
                try:
                    conversation = future.result()
                    progress.update()
                except Exception as error:
                    if num_attempts >= 3:
                        raise

                    logger.error(
                        "Failed attempt %d for entry %s", num_attempts, entry["id"]
                    )
                    logger.error(error)
                    if (
                        type(error).__name__ == "StopCandidateException"
                        and model_entry is model
                    ):
                        temperature = entry.setdefault("params", {}).get(
                            "temperature", 0
                        )
                        temperature = min(temperature + 0.4, 1)
                        logger.warning(
                            "Trying %s again with temperature=%.2f for Google RECITATION error",
                            entry["id"],
                            temperature,
                        )
                        model_entry = _get_model(temperature=temperature)
                        entry["params"]["temperature"] = temperature

                    futures[
                        executor.submit(
                            run_simulation,
                            model_entry,
                            entry,
                            ignore_response=ignore_response,
                        )
                    ] = (
                        entry,
                        num_attempts + 1,
                        model_entry,
                    )
                    continue

                output_path = output_dir / f"{entry['id']}.json"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w") as file:
                    json.dump(
                        {**entry, "conversation": conversation},
                        file,
                        sort_keys=True,
                    )

                logger.info(
                    "Saved conversation for entry %s to %s",
                    entry["id"],
                    output_path,
                )


if __name__ == "__main__":
    logging.basicConfig()
    main()
