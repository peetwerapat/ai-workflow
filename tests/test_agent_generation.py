import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentGenerationTest(unittest.TestCase):
    def test_installer_renders_provider_native_agents_and_reinstalls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout = root / "checkout"
            shutil.copytree(ROOT / "ai", checkout / "ai")
            shutil.copy2(ROOT / "install.sh", checkout / "install.sh")
            homes = {name: root / name for name in ("claude", "codex", "agy", "zcode", "shared")}
            old_agent = homes["claude"] / "agents" / "spec-analyzer.md"
            old_agent.parent.mkdir(parents=True)
            old_agent.symlink_to(checkout / "ai" / "agents" / "spec-analyzer.md")
            source_before = old_agent.read_text()
            environment = os.environ.copy()
            environment.update({
                "AI_AGENT_DEV": "1",
                "AI_AGENT_NO_SHELL": "1",
                "AI_AGENT_HOME": str(root / "store"),
                "CLAUDE_HOME": str(homes["claude"]),
                "CODEX_HOME": str(homes["codex"]),
                "AGY_HOME": str(homes["agy"]),
                "ZCODE_HOME": str(homes["zcode"]),
                "AI_HOME": str(homes["shared"]),
            })
            for _ in range(2):
                subprocess.run(["bash", str(checkout / "install.sh"), "all"], env=environment, check=True, capture_output=True, text=True)

            self.assertEqual((checkout / "ai" / "agents" / "spec-analyzer.md").read_text(), source_before)
            claude = old_agent.read_text()
            self.assertFalse(old_agent.is_symlink())
            self.assertIn("model: sonnet", claude)
            self.assertIn("effort: medium", claude)

            codex = tomllib.loads((homes["codex"] / "agents" / "spec-analyzer.toml").read_text())
            self.assertEqual(codex["model"], "gpt-6-luna")
            self.assertEqual(codex["model_reasoning_effort"], "xhigh")
            self.assertEqual(codex["sandbox_mode"], "read-only")
            self.assertIn("# Spec Analyzer", codex["developer_instructions"])

            agy = (homes["agy"] / "agents" / "spec-analyzer.md").read_text()
            self.assertIn("model: pro", agy)
            self.assertIn("subagent: true", agy)
            self.assertNotIn("effort:", agy)

            zcode = (homes["zcode"] / "agents" / "spec-analyzer.md").read_text()
            self.assertIn("model: inherit", zcode)
            self.assertNotIn("thoughtLevel:", zcode)

            settings = json.loads((checkout / "ai" / "agents" / "models.json").read_text())
            settings["spec-analyzer"]["zcode"] = {"model": "glm-5.3", "effort": "high"}
            (checkout / "ai" / "agents" / "models.json").write_text(json.dumps(settings))
            subprocess.run(["bash", str(checkout / "install.sh"), "zcode"], env=environment, check=True, capture_output=True, text=True)
            self.assertIn("thoughtLevel: high", (homes["zcode"] / "agents" / "spec-analyzer.md").read_text())

    def test_unsupported_effort_preserves_existing_agent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout = root / "checkout"
            shutil.copytree(ROOT / "ai", checkout / "ai")
            shutil.copy2(ROOT / "install.sh", checkout / "install.sh")
            settings_file = checkout / "ai" / "agents" / "models.json"
            settings = json.loads(settings_file.read_text())
            settings["spec-analyzer"]["antigravity"]["effort"] = "high"
            settings_file.write_text(json.dumps(settings))
            destination = root / "agy" / "agents" / "spec-analyzer.md"
            destination.parent.mkdir(parents=True)
            destination.write_text("existing")
            environment = os.environ.copy()
            environment.update({
                "AI_AGENT_DEV": "1",
                "AI_AGENT_NO_SHELL": "1",
                "AI_AGENT_HOME": str(root / "store"),
                "AI_HOME": str(root / "shared"),
                "AGY_HOME": str(root / "agy"),
            })
            result = subprocess.run(
                ["bash", str(checkout / "install.sh"), "antigravity"],
                env=environment, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(destination.read_text(), "existing")


if __name__ == "__main__":
    unittest.main()
