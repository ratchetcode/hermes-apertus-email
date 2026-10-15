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
EMAIL_DRAFT_SKILL_PATH = ROOT / "profile-skills" / "email-draft-workflow" / "SKILL.md"



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
        self.assertIn('HERMES_ENABLE_PROJECT_PLUGINS: "false"', compose)
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
        self.assertIn('if [ ! -f "$runtime_dir/SOUL.md" ]; then', script)
        self.assertNotIn("tui-widgets", script)
        self.assertIn('profile_skills_dir="/workspace/profile-skills"', script)
        self.assertIn('rm -rf "$runtime_dir/skills"', script)
        self.assertIn('cp -R "$profile_skills_dir/." "$runtime_dir/skills/"', script)
        self.assertNotIn("email-framework", script)
        self.assertIn('hermes config set toolsets \'["hermes-cli"]\'', script)
        self.assertIn('if [ "$#" -eq 0 ]; then', script)
        self.assertIn('set -- hermes gateway run --no-supervise --external-supervisor', script)
        self.assertIn('exec "$@"', script)
        self.assertNotIn("/home/nick/.hermes", script)

    def test_profile_skills_contain_only_the_email_draft_workflow(self):
        skills = sorted(path.relative_to(ROOT / "profile-skills").as_posix() for path in (ROOT / "profile-skills").rglob("SKILL.md"))

        self.assertEqual(skills, ["email-draft-workflow/SKILL.md"])
        skill = EMAIL_DRAFT_SKILL_PATH.read_text(encoding="utf-8")
        self.assertIn("no-send", skill)
        self.assertIn("fiktive", skill)

    def test_runtime_template_is_a_minimal_hermes_base_without_email_plugin(self):
        template = HERMES_CONFIG_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("provider: custom", template)
        self.assertIn('default: "${LLM_NAME}"', template)
        self.assertIn('base_url: "${LLM_BASE_URL}"', template)
        self.assertIn('api_key: "${LLM_API_KEY}"', template)
        self.assertNotIn("email-framework", template)
        self.assertNotIn("plugins:", template)
        self.assertNotIn("TELEGRAM_BOT_TOKEN", template)

    def test_soul_template_is_neutral_and_does_not_force_email_onboarding(self):
        soul = SOUL_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("persistent project-local Hermes agent", soul)
        self.assertIn("Do not invent", soul)
        self.assertIn("explicit approval", soul)
        self.assertNotIn("Which language would you like to use?", soul)
        self.assertNotIn("3R", soul)
        self.assertNotIn("email_framework", soul)

    def test_project_rules_keep_runtime_and_credentials_isolated(self):
        rules = AGENTS_PATH.read_text(encoding="utf-8")

        self.assertIn("persistent project-local Hermes runtime", rules)
        self.assertIn("No external actions", rules)
        self.assertIn("Never read, display, copy or commit", rules)
        self.assertNotIn("email-marketing", rules)
        self.assertNotIn("demo-contact-001", rules)

    def test_makefile_keeps_hermes_tui_as_default_run_mode(self):
        makefile = MAKEFILE_PATH.read_text(encoding="utf-8")

        self.assertIn("run:\n\tdocker compose run --rm hermes /bin/sh /workspace/scripts/start-hermes.sh hermes --tui", makefile)
        self.assertNotIn("start-controlled-workflow.sh", makefile)
        self.assertIn("gateway:\n\tdocker compose up", makefile)
        self.assertIn("chat: run", makefile)
        self.assertIn("profile-apply:\n\tpython3 scripts/apply_profile.py", makefile)
        self.assertIn("profile-snapshot:\n\tpython3 scripts/export_profile_snapshot.py", makefile)
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
