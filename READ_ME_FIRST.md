# Read this first

This folder is now an implemented offline-first repository, not merely a Codex build package.

Start with README.md. Create a Python environment, install the development extras, run the tests, and then run:

    python -m learning_plane.cli demo all

The source workbooks belong under docs/private_workbooks and are ignored by Git. Do not publish them. No command in the repository deploys Google Cloud resources or calls a paid model by default.
