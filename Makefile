.POSIX:
SOURCES := src default.nix
INPUTS :=
ENTRYPOINT_DEPS := $(SOURCES) $(INPUTS)

# Porcelain
# ###############
.PHONY: env-up env-down env-recreate container run build lint test watch

watch:
	@echo This is a long running webserver, `run` is actually `watch`
	make --no-print-directory run

run: setup ## run the app
	APP_PGSQL_CONNECTION_STRING="postgresql://user:password@localhost/db" pdm run fastapi dev src/applover_t1/app.py 

env-up: ## set up dev environment
	# https://stackoverflow.com/questions/47207616/auto-remove-container-with-docker-compose-yml
	podman-compose up --force-recreate -V

env-down: ## tear down dev environment
	@echo "Not implemented"; false

env-recreate: env-down env-up ## deconstruct current env and create another one

test: setup ## run all tests
	@echo "Not implemented"; false

container: ## create (and load) container image
	@echo "Not implemented"; false

# Plumbing
# ###############
.PHONY: setup

setup: .venv

.venv: pdm.lock pyproject.toml
	pdm install
	touch .venv

# Utilities
# ###############
.PHONY: help todo clean init
init: ## one time setup
	direnv allow .

clean: ## remove artifacts

help: ## print this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.DEFAULT_GOAL := help
