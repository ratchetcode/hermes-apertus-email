from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PATH = ROOT / "docker-compose.yml"
MAKEFILE_PATH = ROOT / "Makefile"
DRAFT_START_SCRIPT_PATH = ROOT / "scripts" / "start-demo.sh"
HERMES_START_SCRIPT_PATH = ROOT / "scripts" / "start-hermes.sh"
HERMES_CONFIG_TEMPLATE_PATH = ROOT / "runtime-template" / "config.yaml"
SOUL_TEMPLATE_PATH = ROOT / "runtime-template" / "SOUL.md"
AGENTS_PATH = ROOT / "AGENTS.md"



class ContainerStartTests(unittest.TestCase):
    def test_compose_starts_an_isolated_persistent_hermes_gateway(self):
        compose = COMPOSE_PATH.read_text(encoding="utf-8")

        self.assertIn('entrypoint: ["/opt/hermes/docker/entrypoint-dispatch.sh"]', compose)
        self.assertIn('command: ["/bin/sh", "/workspace/scripts/start-hermes.sh"]', compose)
        self.assertIn("stdin_open: true", compose)
        self.assertIn("tty: true", compose)
        self.assertNotIn("user:", compose)
        self.assertNotIn("init: true", compose)
        self.assertIn('HERMES_UID: "${HERMES_UID:-1000}"', compose)
        self.assertIn('HERMES_GID: "${HERMES_GID:-1000}"', compose)
        self.assertIn("HERMES_HOME: /opt/data", compose)
        self.assertIn("\n      HOME: /opt/data", compose)
        self.assertIn('HERMES_ENABLE_PROJECT_PLUGINS: "true"', compose)
        self.assertNotIn("HERMES_TUI_DIR", compose)
        self.assertIn("- ./runtime/hermes:/opt/data", compose)
        self.assertIn("- ./:/workspace:ro", compose)
        self.assertNotIn("container_name:", compose)

    def test_gateway_start_script_bootstraps_only_project_local_runtime(self):
        script = HERMES_START_SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn('runtime_dir="${HERMES_HOME:-/opt/data}"', script)
        self.assertIn('template="/workspace/runtime-template/config.yaml"', script)
        self.assertIn('cp "$template" "$runtime_dir/config.yaml"', script)
        self.assertIn('soul_template="/workspace/runtime-template/SOUL.md"', script)
        self.assertIn('cp "$soul_template" "$runtime_dir/SOUL.md"', script)
        self.assertIn('"$runtime_dir/.email-framework-soul-v10"', script)
        self.assertNotIn("tui-widgets", script)
        self.assertIn("hermes config set plugins.enabled", script)
        self.assertIn("hermes config set toolsets", script)
        self.assertIn('if [ "$#" -eq 0 ]; then', script)
        self.assertIn('set -- hermes gateway run --no-supervise --external-supervisor', script)
        self.assertIn('exec "$@"', script)
        self.assertNotIn("/home/nick/.hermes", script)

    def test_runtime_template_uses_only_local_environment_references_for_apertus(self):
        template = HERMES_CONFIG_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("provider: custom", template)
        self.assertIn('default: "${LLM_NAME}"', template)
        self.assertIn('base_url: "${LLM_BASE_URL}"', template)
        self.assertIn('api_key: "${LLM_API_KEY}"', template)
        self.assertNotIn("TELEGRAM_BOT_TOKEN", template)

    def test_soul_template_requires_reply_in_the_operator_language(self):
        soul = SOUL_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("selected language", soul)
        self.assertIn("every following question and response", soul)
        self.assertIn("language is also the campaign draft language", soul)
        self.assertIn("first question", soul)
        self.assertIn("Which language would you like to use?", soul)
        self.assertIn("one unanswered item per turn", soul)
        self.assertIn("/email-approve <approval-id>", soul)
        self.assertIn("`recruit`, `retain` or `recover`", soul)
        self.assertIn("/email-approve-segment <approval-id>", soul)
        self.assertNotIn("Möchten Sie eine kurze Einführung", soul)
        self.assertIn("Do not invent defaults", soul)
        self.assertIn("Never expose tool names", soul)
        self.assertIn("immediately call `email_framework_segment_preflight`", soul)

    def test_project_rules_require_preflight_and_fresh_follow_up_approval(self):
        rules = AGENTS_PATH.read_text(encoding="utf-8")

        self.assertIn("controlled email-marketing", rules)
        self.assertIn("python3 /workspace/src/workflow.py --contact-id demo-contact-001", rules)
        self.assertIn("new, explicit confirmation", rules)
        self.assertIn("follow-up email is a new draft", rules)
        self.assertIn("No email sending", rules)

    def test_makefile_exposes_interactive_default_and_separate_gateway_mode(self):
        makefile = MAKEFILE_PATH.read_text(encoding="utf-8")

        self.assertIn("docker compose run --rm hermes /bin/sh /workspace/scripts/start-hermes.sh hermes --tui", makefile)
        self.assertIn("workflow:\n\tdocker compose run --rm hermes /bin/sh /workspace/scripts/start-controlled-workflow.sh", makefile)
        self.assertIn("gateway:\n\tdocker compose up", makefile)
        self.assertIn("chat: run", makefile)
        self.assertIn("docker compose run --rm hermes /bin/sh /workspace/scripts/start-demo.sh", makefile)
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
