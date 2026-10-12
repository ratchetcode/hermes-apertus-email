.PHONY: run chat gateway draft stop logs test

# Default judge/operator path: start an isolated interactive Hermes session.
run:
	docker compose run --rm --entrypoint /bin/sh hermes /workspace/scripts/start-hermes.sh hermes --tui

# Alias for the interactive default.
chat: run

# Persistent gateway for a separately configured messaging platform.
gateway:
	docker compose up

# Deterministic policy preflight; live Apertus generation remains opt-in.
draft:
	docker compose run --rm --entrypoint /workspace/scripts/start-demo.sh hermes

stop:
	docker compose down --remove-orphans

logs:
	docker compose logs -f

test:
	python3 -m unittest discover -s tests -v