from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PATH = ROOT / "docker-compose.yml"
START_SCRIPT_PATH = ROOT / "scripts" / "start-demo.sh"


class InteractiveContainerStartTests(unittest.TestCase):
    def test_compose_runs_the_interactive_start_script_with_a_tty(self):
        compose = COMPOSE_PATH.read_text(encoding="utf-8")

        self.assertIn("stdin_open: true", compose)
        self.assertIn("tty: true", compose)
        self.assertIn('entrypoint: ["/bin/sh", "/workspace/scripts/start-demo.sh"]', compose)
        self.assertIn("init: true", compose)
        self.assertIn('user: "${HERMES_UID:-1000}:${HERMES_GID:-1000}"', compose)
        self.assertNotIn("HERMES_UID=${HERMES_UID:-1000}", compose)
        self.assertNotIn("HERMES_GID=${HERMES_GID:-1000}", compose)
        self.assertNotIn("gateway run", compose)

    def test_start_script_prints_the_demo_boundary_then_starts_cli(self):
        script = START_SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("Hermes × Apertus – Controlled Email Drafting Demo", script)
        self.assertIn("Niemals E-Mails versenden", script)
        self.assertIn("/workspace/AGENTS.md", script)
        self.assertIn(': "${LLM_NAME:?LLM_NAME must be set in .env}"', script)
        self.assertIn(': "${LLM_BASE_URL:?LLM_BASE_URL must be set in .env}"', script)
        self.assertIn(': "${LLM_API_KEY:?LLM_API_KEY must be set in .env}"', script)
        self.assertIn('hermes config set model.default "$LLM_NAME"', script)
        self.assertIn("hermes config set model.provider custom", script)
        self.assertIn('hermes config set model.base_url "$LLM_BASE_URL"', script)
        self.assertIn("hermes config set model.api_key '${LLM_API_KEY}'", script)
        self.assertIn("exec hermes --cli", script)
    def test_make_run_uses_an_attached_one_off_container(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn("docker compose run --rm hermes", makefile)
        self.assertNotIn("docker compose up", makefile)


if __name__ == "__main__":
    unittest.main()
