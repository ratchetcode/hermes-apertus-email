from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PATH = ROOT / "docker-compose.yml"
MAKEFILE_PATH = ROOT / "Makefile"
DRAFT_START_SCRIPT_PATH = ROOT / "scripts" / "start-demo.sh"
HERMES_START_SCRIPT_PATH = ROOT / "scripts" / "start-hermes.sh"
HERMES_CONFIG_TEMPLATE_PATH = ROOT / "runtime-template" / "config.yaml"
AGENTS_PATH = ROOT / "AGENTS.md"



class ContainerStartTests(unittest.TestCase):
    def test_compose_starts_an_isolated_persistent_hermes_gateway(self):
        compose = COMPOSE_PATH.read_text(encoding="utf-8")

        self.assertIn('entrypoint: ["/bin/sh", "/workspace/scripts/start-hermes.sh"]', compose)
        self.assertIn("stdin_open: true", compose)
        self.assertIn("tty: true", compose)
        self.assertIn("init: true", compose)
        self.assertIn('user: "${HERMES_UID:-1000}:${HERMES_GID:-1000}"', compose)
        self.assertIn("HERMES_HOME: /opt/data", compose)
        self.assertIn("\n      HOME: /opt/data", compose)
        self.assertIn("- ./runtime/hermes:/opt/data", compose)
        self.assertIn("- ./:/workspace:ro", compose)
        self.assertNotIn("container_name:", compose)

    def test_gateway_start_script_bootstraps_only_project_local_runtime(self):
        script = HERMES_START_SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn('runtime_dir="${HERMES_HOME:-/opt/data}"', script)
        self.assertIn('template="/workspace/runtime-template/config.yaml"', script)
        self.assertIn('cp "$template" "$runtime_dir/config.yaml"', script)
        self.assertIn('if [ "$#" -eq 0 ]; then', script)
        self.assertIn('set -- hermes gateway run --no-supervise --external-supervisor', script)
        self.assertIn('exec "$@"', script)
        self.assertNotIn("/home/nick/.hermes", script)
        self.assertNotIn("hermes config set", script)

    def test_runtime_template_uses_only_local_environment_references_for_apertus(self):
        template = HERMES_CONFIG_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("provider: custom", template)
        self.assertIn('default: "${LLM_NAME}"', template)
        self.assertIn('base_url: "${LLM_BASE_URL}"', template)
        self.assertIn('api_key: "${LLM_API_KEY}"', template)
        self.assertNotIn("TELEGRAM_BOT_TOKEN", template)

    def test_project_rules_require_preflight_and_fresh_follow_up_approval(self):
        rules = AGENTS_PATH.read_text(encoding="utf-8")

        self.assertIn("controlled email-marketing", rules)
        self.assertIn("python3 /workspace/src/workflow.py --contact-id demo-contact-001", rules)
        self.assertIn("new, explicit confirmation", rules)
        self.assertIn("follow-up email is a new draft", rules)
        self.assertIn("No email sending", rules)

    def test_makefile_exposes_interactive_default_and_separate_gateway_mode(self):
        makefile = MAKEFILE_PATH.read_text(encoding="utf-8")

        self.assertIn("docker compose run --rm --entrypoint /bin/sh hermes /workspace/scripts/start-hermes.sh hermes --tui", makefile)
        self.assertIn("gateway:\n\tdocker compose up", makefile)
        self.assertIn("chat: run", makefile)
        self.assertIn("docker compose run --rm --entrypoint /workspace/scripts/start-demo.sh hermes", makefile)
        self.assertNotIn("run:\n\tdocker compose up", makefile)

    def test_draft_start_script_keeps_the_explicit_live_confirmation_gate(self):
        script = DRAFT_START_SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("Apertus Draft Gate – Controlled Email Drafting Demo", script)
        self.assertIn("Niemals E-Mails versenden", script)
        self.assertIn("/workspace/AGENTS.md", script)
        self.assertIn(': "${LLM_NAME:?LLM_NAME must be set in .env}"', script)
        self.assertIn(': "${LLM_BASE_URL:?LLM_BASE_URL must be set in .env}"', script)
        self.assertIn(': "${LLM_API_KEY:?LLM_API_KEY must be set in .env}"', script)
        self.assertIn("python3 /workspace/src/workflow.py --contact-id demo-contact-001", script)
        self.assertIn("Generate a live Apertus draft? [y/N]", script)
        self.assertIn("--live", script)
        self.assertNotIn("hermes config set", script)


if __name__ == "__main__":
    unittest.main()
