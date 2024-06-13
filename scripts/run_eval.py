from __future__ import annotations

import concurrent.futures
import json
import logging
import pathlib
from typing import Any

import click
import ruamel.yaml
import tqdm

from darkgpt.agents import Overseer
from darkgpt.models import ModelRegistry

logger = logging.getLogger(__name__)


def _load_conversations(conversations_dir: pathlib.Path, limit: int | None = None):
    for idx_file, filename in enumerate(conversations_dir.glob("*.json"), 1):
        with open(filename, "r") as f:
            entry = json.load(f)
        yield entry

        if limit and idx_file >= limit:
            break


def _evaluate(overseer: Overseer, entry: dict, **prompt_variables):
    logger.info("Evaluating entry %s", entry["id"])
    try:
        eval, conversation = overseer.evaluate(entry, **prompt_variables)
    except Exception as error:
        logger.error("Error evaluating entry %s: %s", entry["id"], error)
        raise error
    result = {
        **eval,
        **{
            key: {
                issue_type: bool(value)
                for issue_type, value in sorted(eval[key].items())
            }
            for key in ("ethical_issues", "meta")
        },
        "id": entry["id"],
        "conversation": conversation,
    }
    return result


@click.command()
@click.option(
    "--overseer",
    "overseer_name",
    required=True,
    help="The model to use for the simulation",
)
@click.option(
    "--assistant",
    "assistant_name",
    required=True,
    help="The model being evaluated",
)
@click.option(
    "--conversations-dir",
    type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path),
    required=True,
    help="Directory of conversations between users and chatbot.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    required=True,
    help="Path to output directory of the overseer's evaluation results",
)
@click.option(
    "--params-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    default="params.yaml",
    help="file containing model parameters",
)
@click.option(
    "--limit",
    type=int,
    help="Limit the number of conversations to evaluate",
)
@click.option("--max-workers", type=int, default=50)
def main(
    overseer_name: str,
    assistant_name: str,
    conversations_dir: pathlib.Path,
    output_dir: pathlib.Path,
    params_file: pathlib.Path,
    limit: int | None,
    max_workers: int,
):
    """Evaluates the presence of dark patterns in a conversation."""

    yaml = ruamel.yaml.YAML(typ="safe")
    with open(params_file, "r") as file:
        params: dict[str, Any] = yaml.load(file)
    model_params: dict[str, Any] = params["models"]
    issues: dict[str, dict[str, str]] = params["eval"]["issues"]

    overseer_params: dict[str, Any] = model_params[overseer_name]["build"]
    overseer_name = overseer_params.pop("model_name", overseer_name)
    model_type = overseer_params.pop("type")
    logger.info(
        "Using %s model %s with args %s", model_type, overseer_name, overseer_params
    )
    model = ModelRegistry.get(model_type, model_name=overseer_name, **overseer_params)

    overseer = Overseer(model, issues, model_params[assistant_name]["prompt_info"])

    output_dir.mkdir(parents=True, exist_ok=True)
    yaml.default_flow_style = False
    with (
        concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor,
        tqdm.tqdm(total=limit if limit else None) as progress,
    ):
        futures = {
            executor.submit(_evaluate, overseer, entry): (
                entry,
                1,
            )
            for entry in _load_conversations(conversations_dir, limit=limit)
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
                except Exception as error:
                    logger.error(
                        "Failed attempt %d for entry %s: %s",
                        num_attemps,
                        entry_id,
                        str(error),
                    )
                    if num_attemps < 3:
                        futures[executor.submit(_evaluate, overseer, entry)] = (
                            entry,
                            num_attemps + 1,
                        )
                        continue

                    eval_result = {
                        **entry,
                        "error": {
                            "type": type(error).__name__,
                            "message": str(error),
                        },
                    }
                else:
                    logger.info(
                        "Id: %s Result: %s",
                        entry_id,
                        json.dumps(
                            eval_result["ethical_issues"], indent=4, sort_keys=True
                        ),
                    )

                progress.update()
                output_path = output_dir / f"{entry_id}.yaml"
                with open(output_path, "w") as file:
                    yaml.dump(eval_result, file)
                logger.info("Saved result to %s", output_path)


if __name__ == "__main__":
    logging.basicConfig()
    main()
