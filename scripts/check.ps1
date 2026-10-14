$ErrorActionPreference = 'Stop'
ruff check .
ruff format --check .
pytest -q
python -m learning_plane.cli demo all

