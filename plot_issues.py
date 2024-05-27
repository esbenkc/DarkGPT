import pathlib
from collections import defaultdict

import matplotlib.pyplot as plt
import ruamel.yaml
from absl import app, flags

FLAGS = flags.FLAGS

colors = {
    "claude-3-sonnet": "#ff9d00",
    "gpt-4-turbo": "#3a88ff",
}


def main(_):
    results = defaultdict(lambda: defaultdict(int))
    yaml = ruamel.yaml.YAML()
    issues = set()
    for metrics_file in pathlib.Path(FLAGS.metrics_dir).rglob("*.yaml"):
        assistant_model = pathlib.Path(metrics_file).stem
        with metrics_file.open() as file:
            data: dict[str, dict[str, int]] = yaml.load(file)
        for issue, overseers in data.items():
            for overseer, issue_count in overseers.items():
                results[(assistant_model, overseer)][issue] += issue_count
                issues.add(issue)

    issues = sorted(issues)
    model_pairs = {
        model_pair: " x ".join(model.split("-202")[0] for model in model_pair)
        for model_pair in sorted(results, key=lambda mp: (mp[0], mp[0] != mp[1]))
    }

    fig, ax = plt.subplots(
        ncols=1, nrows=1, figsize=(20, 5), squeeze=True, tight_layout=True
    )
    issue_positions = list(range(len(issues)))
    bar_width = 0.2
    for idx_pair, (model_pair, label) in enumerate(model_pairs.items()):
        model_issues = results[model_pair]
        ax.bar(
            [pos + idx_pair * bar_width for pos in issue_positions],
            [model_issues[issue] for issue in issues],
            bar_width,
            label=label,
            color=colors[label.split(" x ")[0]],
            alpha=0.6 if model_pair[0] != model_pair[1] else 1,
            hatch="x" if model_pair[0] != model_pair[1] else "",
            edgecolor="black",
        )

    ax.set_xlabel("Issues")
    ax.set_ylabel("Counts")
    ax.set_title("Issues by model and overseer")
    ax.set_xticks(
        [pos + 0.5 * (len(model_pairs) - 1) * bar_width for pos in issue_positions]
    )
    ax.set_xticklabels(issues)
    ax.legend()

    output_file = pathlib.Path(FLAGS.output_file)
    output_file.parent.mkdir(exist_ok=True)
    fig.savefig(output_file)


if __name__ == "__main__":
    flags.DEFINE_string(
        "metrics_dir", None, "Directory containing metrics files", required=True
    )
    flags.DEFINE_string("output_file", None, "Output file", required=True)
    app.run(main)
