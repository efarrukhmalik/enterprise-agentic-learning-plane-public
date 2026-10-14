.PHONY: install test lint demo api
install:
	python -m pip install --require-hashes -r requirements-dev.lock
	python -m pip install --no-deps --no-build-isolation -e .
test:
	pytest -q
lint:
	ruff check . && ruff format --check .
demo:
	python -m learning_plane.cli demo all
api:
	uvicorn learning_plane.api.app:app --reload

