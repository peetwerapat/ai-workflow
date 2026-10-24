import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/tools"))
import installation


class InstallationTest(unittest.TestCase):
    def setup_checkout(self, root, dev=True):
        checkout = root / "checkout"
        shutil.copytree(ROOT / "ai", checkout / "ai")
        shutil.copy2(ROOT / "install.sh", checkout / "install.sh")
        env = os.environ.copy()
        for key in ("AI_AGENT_TRANSACTION", "AI_AGENT_SELF_INSTALLED", "AI_AGENT_FROM", "AI_AGENT_DEV"):
            env.pop(key, None)
        env.update({"AI_AGENT_NO_SHELL": "1", "AI_AGENT_YES": "1",
                    "AI_AGENT_HOME": str(root / "store"), "AI_HOME": str(root / "shared"),
                    "CLAUDE_HOME": str(root / "claude"), "CODEX_HOME": str(root / "codex"),
                    "AGY_HOME": str(root / "agy"), "ZCODE_HOME": str(root / "zcode")})
        if dev:
            env["AI_AGENT_DEV"] = "1"
        return checkout, env

    def run_install(self, checkout, env, command, success=True):
        result = subprocess.run(["bash", str(checkout / "install.sh"), command],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def test_doctor_detects_tampered_generated_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout, env = self.setup_checkout(root)
            self.run_install(checkout, env, "codex")
            self.run_install(checkout, env, "--doctor")
            target = root / "codex/agents/spec-analyzer.toml"
            target.write_text("tampered")
            result = self.run_install(checkout, env, "--doctor", success=False)
            self.assertIn("Missing/modified artifact", result.stdout)

    def test_partial_reinstall_does_not_hide_stale_other_provider(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout, env = self.setup_checkout(root)
            self.run_install(checkout, env, "all")
            source = checkout / "ai/agents/spec-analyzer.md"
            source.write_text(source.read_text() + "\nNew instruction.\n")
            self.run_install(checkout, env, "codex")
            report = self.run_install(checkout, env, "--doctor", success=False)
            self.assertIn("reinstall claude", report.stdout)
            self.assertNotIn("reinstall codex", report.stdout)

    def test_failed_install_restores_files_already_changed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout, env = self.setup_checkout(root)
            target = root / "codex/AGENTS.md"
            target.parent.mkdir(parents=True)
            target.write_text("user rules")
            script = checkout / "install.sh"
            script.write_text(script.read_text().replace('  ok "$CODEX_HOME/AGENTS.md"',
                                                        '  return 9 # injected failure'))
            self.run_install(checkout, env, "codex", success=False)
            self.assertFalse(target.is_symlink())
            self.assertEqual(target.read_text(), "user rules")
            self.assertFalse((root / "shared").exists())

    def test_rollback_restores_prior_source_and_provider_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout, env = self.setup_checkout(root, dev=False)
            self.run_install(checkout, env, "codex")
            old_source = (root / "store/ai/agents/spec-analyzer.md").read_text()
            old_agent = (root / "codex/agents/spec-analyzer.toml").read_text()
            source = checkout / "ai/agents/spec-analyzer.md"
            source.write_text(source.read_text() + "\nUpdated prompt.\n")
            self.run_install(checkout, env, "codex")
            self.assertNotEqual((root / "codex/agents/spec-analyzer.toml").read_text(), old_agent)
            self.run_install(root / "store", env, "--rollback")
            self.assertEqual((root / "store/ai/agents/spec-analyzer.md").read_text(), old_source)
            self.assertEqual((root / "codex/agents/spec-analyzer.toml").read_text(), old_agent)
            self.run_install(root / "store", env, "--doctor")

    def test_rollback_refuses_to_overwrite_later_user_edits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout, env = self.setup_checkout(root)
            self.run_install(checkout, env, "codex")
            target = root / "codex/agents/spec-analyzer.toml"
            target.write_text("developer's newer edit")
            self.run_install(checkout, env, "--rollback", success=False)
            self.assertEqual(target.read_text(), "developer's newer edit")

    def test_invalid_source_fails_before_install_mutations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout, env = self.setup_checkout(root)
            config = checkout / "ai/agents/models.json"
            values = json.loads(config.read_text())
            values["spec-analyzer"]["codex"]["effort"] = "typo"
            config.write_text(json.dumps(values))
            self.run_install(checkout, env, "all", success=False)
            self.assertFalse((root / "store").exists())
            self.assertFalse((root / "codex").exists())

    def test_rollback_preserves_unrelated_provider_edits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout, env = self.setup_checkout(root)
            unrelated = root / "claude/CLAUDE.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("original")
            self.run_install(checkout, env, "codex")
            unrelated.write_text("new unrelated work")
            self.run_install(checkout, env, "--rollback")
            self.assertEqual(unrelated.read_text(), "new unrelated work")

    def test_skill_file_symlink_cannot_overwrite_its_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout, env = self.setup_checkout(root)
            source = root / "custom.md"
            source.write_text("<!-- generated by ai-agent -->\nKeep this source.\n")
            skill = root / "codex/skills/spec/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.symlink_to(source)
            self.run_install(checkout, env, "codex")
            self.assertIn("Keep this source.", source.read_text())
            self.assertFalse(skill.is_symlink())
            self.assertIn("name: spec", skill.read_text())

    def test_corrupt_snapshot_is_rejected_before_replacing_current_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout, env = self.setup_checkout(root)
            target = root / "codex/AGENTS.md"
            target.parent.mkdir(parents=True)
            target.write_text("old rules")
            self.run_install(checkout, env, "codex")
            snapshot = Path((root / ".store-history/latest").read_text().strip())
            entries = json.loads((snapshot / "snapshot.json").read_text())["entries"]
            index = next(i for i, entry in enumerate(entries) if entry["path"] == str(target))
            (snapshot / str(index)).write_text("corrupted backup")
            self.run_install(checkout, env, "--rollback", success=False)
            self.assertTrue(target.is_symlink())
            self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
