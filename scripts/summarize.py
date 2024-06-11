import pathlib
from collections import defaultdict

import ruamel.yaml
from absl import app, flags

FLAGS = flags.FLAGS


def main(_):
    output_file = pathlib.Path(FLAGS.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    yaml = ruamel.yaml.YAML(typ="safe")
    yaml.default_flow_style = False
    manifest_file, category = str(FLAGS.manifest).split(":", 1)
    with open(manifest_file, "r") as file:
        prompt_ids: list[str] = yaml.load(file)[category]

    with open(FLAGS.params_file, "r") as file:
        overseers: list[str] = yaml.load(file)["eval"]["overseers"]

    metrics = defaultdict(lambda: defaultdict(int))
    for prompt_id in prompt_ids:
        for overseer in overseers:
            eval_file = f"{FLAGS.evals_dir}/{overseer}/{prompt_id}.yaml"
            with open(eval_file, "r") as file:
                content: dict[str, bool] = yaml.load(file)["ethical_issues"]

            for key, value in content.items():
                metrics[key][overseer] += value

    averages = {
        key: {overseer: count for overseer, count in sorted(values.items())}
        for key, values in sorted(metrics.items())
    }

    with open(output_file, "w") as file:
        yaml.dump(averages, file)


if __name__ == "__main__":
    flags.DEFINE_string(
        "evals_dir", None, "Directory containing eval files", required=True
    )
    flags.DEFINE_string("output_file", None, "Output YAML file name", required=True)
    flags.DEFINE_string(
        "manifest",
        None,
        "Prompt manifest file and category as path/to/file:category",
    )
    flags.DEFINE_string("params_file", "params.yaml", "Params file")
    app.run(main)
