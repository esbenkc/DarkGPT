## Repo Setup
1. Clone the repo
2. Open the repo in Cursor or VS Code and run "Reopen in Container"
    - Make sure you have the Remote: Dev Containers extension and Docker installed
    - If you insist on not using Docker, run `poetry install`
3. Run `dvc pull` to pull all the data

The pipeline is outlined in `dvc.yaml` using the parameters in `params.yaml`. Refer to [the DVC documentation](https://dvc.org/doc) for detailed instructions on how to use DVC.

