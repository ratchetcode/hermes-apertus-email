import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from profile_snapshot import apply_profile_to_runtime, export_profile_snapshot


class ProfileSnapshotTests(unittest.TestCase):
    def test_applies_versioned_profile_without_touching_runtime_state_or_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "agent-profile"
            runtime = root / "runtime"
            (profile / "instructions").mkdir(parents=True)
            (profile / "SOUL.md").write_text("# Versionierte SOUL\n", encoding="utf-8")
            (profile / "config.yaml").write_text(
                "model:\n  api_key: \"${LLM_API_KEY}\"\n", encoding="utf-8"
            )
            (profile / "instructions" / "email-workflow.md").write_text(
                "# Kontrollierter Entwurfsablauf\n", encoding="utf-8"
            )
            (runtime / "instructions").mkdir(parents=True)
            (runtime / ".env").write_text("LLM_API_KEY=private\n", encoding="utf-8")
            (runtime / "state.db").write_text("private state", encoding="utf-8")
            (runtime / "sessions").mkdir()
            (runtime / "sessions" / "chat.jsonl").write_text("private chat", encoding="utf-8")
            (runtime / "instructions" / "obsolete.md").write_text("old", encoding="utf-8")

            result = apply_profile_to_runtime(profile, runtime)

            self.assertEqual(result["files"], ["SOUL.md", "config.yaml", "instructions/email-workflow.md"])
            self.assertEqual((runtime / "SOUL.md").read_text(encoding="utf-8"), "# Versionierte SOUL\n")
            self.assertTrue((runtime / "instructions" / "email-workflow.md").exists())
            self.assertFalse((runtime / "instructions" / "obsolete.md").exists())
            self.assertEqual((runtime / ".env").read_text(encoding="utf-8"), "LLM_API_KEY=private\n")
            self.assertTrue((runtime / "state.db").exists())
            self.assertTrue((runtime / "sessions" / "chat.jsonl").exists())

    def test_exports_only_profile_sources_not_chats_or_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            output = root / "agent-profile"
            (runtime / "instructions").mkdir(parents=True)
            (runtime / "SOUL.md").write_text("# Meine SOUL\n", encoding="utf-8")
            (runtime / "config.yaml").write_text(
                "model:\n  api_key: \"${LLM_API_KEY}\"\n", encoding="utf-8"
            )
            (runtime / "instructions" / "email-workflow.md").write_text(
                "# Entwurfsablauf\nKein Versand.\n", encoding="utf-8"
            )
            (runtime / "state.db").write_text("private session state", encoding="utf-8")
            (runtime / "sessions").mkdir()
            (runtime / "sessions" / "chat.jsonl").write_text("private chat", encoding="utf-8")

            result = export_profile_snapshot(runtime, output)

            self.assertEqual(result["files"], ["SOUL.md", "config.yaml", "instructions/email-workflow.md"])
            self.assertTrue((output / "SOUL.md").exists())
            self.assertTrue((output / "instructions" / "email-workflow.md").exists())
            self.assertFalse((output / "state.db").exists())
            self.assertFalse((output / "sessions").exists())

    def test_refuses_a_literal_secret_in_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            runtime.mkdir()
            (runtime / "SOUL.md").write_text("# SOUL\n", encoding="utf-8")
            (runtime / "config.yaml").write_text(
                "model:\n  api_key: super-secret-value\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "literal secret"):
                export_profile_snapshot(runtime, Path(directory) / "agent-profile")


if __name__ == "__main__":
    unittest.main()
