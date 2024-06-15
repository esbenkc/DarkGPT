from __future__ import annotations

import collections
import concurrent.futures
import itertools
import pathlib
from typing import Any, cast

import click
import matplotlib.pyplot as plt
import ruamel.yaml


@click.command()
@click.argument(
    "METRICS_DIR",
    type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path),
)
@click.argument("GROUP_NAME")
@click.argument(
    "OUTPUT_FILE",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--prompt-manifest-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    default="data/prompts/manifest.yaml",
)
@click.option(
    "--params-file",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    default="params.yaml",
)
def main(
    metrics_dir: pathlib.Path,
    group_name: str,
    output_file: pathlib.Path,
    prompt_manifest_file: pathlib.Path,
    params_file: pathlib.Path,
):
    yaml = ruamel.yaml.YAML()
    with prompt_manifest_file.open() as file:
        prompts: dict[str, list[str]] = yaml.load(file)
    with params_file.open() as file:
        params: dict[str, Any] = yaml.load(file)
    overseers: list[str] = params["eval"]["overseers"]
    categories: list[str] = [*params["eval"]["issues"]]
    plot_params: dict[str, Any] = params["plot"]
    group_params: dict[str, Any] = plot_params["groups"][group_name]
    assistants: list[str] = [model_name for model_name in group_params["models"]]

    eval_files = [
        metrics_dir / category / f"{assistant}.yaml"
        for assistant in assistants
        for category in prompts
    ]

    with concurrent.futures.ThreadPoolExecutor() as pool:
        eval_results = list(
            pool.map(lambda f: ruamel.yaml.YAML(typ="safe").load(f.open()), eval_files)
        )

    issue_counts = collections.defaultdict(collections.Counter)
    for eval_file, eval_result in zip(eval_files, eval_results):
        for overseer in overseers:
            for category in categories:
                issue_counts[(eval_file.stem, overseer)][category] += eval_result[
                    category
                ][overseer]

    fig_params = plot_params["fig"]
    group_width = fig_params.pop("group_width")
    bar_width = group_width / (len(assistants) * len(overseers))
    issue_positions = list(range(len(categories)))

    figsize: tuple[int, int] = fig_params.pop("figsize")
    fig, ax = cast(
        tuple[plt.Figure, plt.Axes],
        plt.subplots(
            ncols=1,
            nrows=1,
            figsize=(figsize[0] * len(categories), figsize[1]),
            squeeze=True,
            tight_layout=True,
            **fig_params,
        ),
    )

    for idx_pair, (assistant, overseer) in enumerate(
        itertools.product(group_params["models"], overseers)
    ):
        y = [issue_counts[(assistant, overseer)][category] for category in categories]
        yerr = [
            (
                num_prompts := len(
                    prompts[
                        "cost_optimisation_answer_length"
                        if "cost_optimization" in category
                        else category
                    ]
                )
            )
            * (
                ((p_issue := num_issues / num_prompts) * (1 - p_issue) / num_prompts)
                ** 0.5
            )
            for category, num_issues in zip(categories, y)
        ]
        ax.bar(
            [
                pos - 0.5 * group_width + (idx_pair * bar_width)
                for pos in issue_positions
            ],
            y,
            bar_width,
            yerr=yerr,
            label=f"{assistant} x {overseer}",
            facecolor=f"#{plot_params['styles'][assistant]['color']}",
            edgecolor=f"#{plot_params['styles'][overseer]['color']}",
            alpha=0.8,
            linewidth=1,
            hatch="xxx",
        )

    ax.set_xlabel("Issues")
    ax.set_ylabel("Counts")
    ax.set_title(f"Issues in {group_params['name']} models")
    ax.set_xticks([pos - 0.5 * bar_width for pos in issue_positions])
    ax.set_xticklabels([*categories])
    ax.set_xlim(
        -(0.5 * group_width + bar_width),
        len(categories) - 1 + 0.5 * group_width,
    )
    ax.legend()
    output_file.parent.mkdir(exist_ok=True, parents=True)
    fig.savefig(output_file)


if __name__ == "__main__":
    main()
