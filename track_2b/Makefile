.PHONY: run chat workflow gateway draft stop logs test

# Hermes TUI, including standard slash commands such as /exit.
run:
	docker compose run --rm hermes /bin/sh /workspace/scripts/start-hermes.sh hermes --tui

# Alias for the interactive Hermes TUI.
chat: run

# Temporary deterministic terminal workflow; not the Hermes TUI.
workflow:
	docker compose run --rm hermes /bin/sh /workspace/scripts/start-controlled-workflow.sh

# Persistent gateway for a separately configured messaging platform.
gateway:
	docker compose up

# Deterministic policy preflight; live Apertus generation remains opt-in.
draft:
	docker compose run --rm hermes /bin/sh /workspace/scripts/start-demo.sh

stop:
	docker compose down --remove-orphans

logs:
	docker compose logs -f

test:
	python3 -m unittest discover -s tests -v