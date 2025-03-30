.PHONY: clean build format run help
.DEFAULT_GOAL := help

help: ## Displays this help message.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

run: ## Runs the development server with the development config
	uv run --group dev d2rloader

format: ## Sorts the imports and reformats the code
	# sort imports / remove unused
	uv run ruff check --fix --select I
	uv run ruff check --fix
	# reformat
	uv run ruff format

build: ## Creates distribution packages (bdist_wheel, sdist)
	uv sync --group build
	uv build

clean: ## Remove unwanted stuff such as __pycache__, etc...
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '.ruff_cache' -exec rm -rf {} +
