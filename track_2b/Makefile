.PHONY: run chat gateway draft profile-apply profile-snapshot stop logs test

# Hermes TUI with the persistent project-local runtime, chats and profile context.
run:
	docker compose run --rm hermes /bin/sh /workspace/scripts/start-hermes.sh hermes --tui

# Alias for the interactive Hermes TUI.
chat: run

# Persistent gateway for a separately configured messaging platform.
gateway:
	docker compose up

# Deterministic policy preflight; live Apertus generation remains opt-in.
draft:
	docker compose run --rm hermes /bin/sh /workspace/scripts/start-demo.sh

# Applies the reviewed Git-versioned profile without touching chats, state or credentials.
profile-apply:
	python3 scripts/apply_profile.py

# Exports only SOUL.md, config.yaml and runtime/hermes/instructions/*.md.
# Chats, state, logs and credentials stay ignored and local.
profile-snapshot:
	python3 scripts/export_profile_snapshot.py

stop:
	docker compose down --remove-orphans

logs:
	docker compose logs -f

test:
	python3 -m unittest discover -s tests -v
