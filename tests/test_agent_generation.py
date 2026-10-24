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
            configured = json.loads((checkout / "ai/agents/models.json").read_text())["spec-analyzer"]["codex"]
            self.assertEqual(codex["model"], configured["model"])
            self.assertEqual(codex["model_reasoning_effort"], configured["effort"])
            self.assertEqual(codex["sandbox_mode"], "read-only")
            self.assertIn("# Spec Analyzer", codex["developer_instructions"])

            agy = (homes["agy"] / "agents" / "spec-analyzer.md").read_text()
            self.assertIn("model: pro", agy)
            self.assertIn("subagent: true", agy)
            self.assertNotIn("effort:", agy)

            zcode = (homes["zcode"] / "agents" / "spec-analyzer.md").read_text()
            self.assertIn("model: inherit", zcode)
            self.assertNotIn("thoughtLevel:", zcode)

            settings = json.loads((checkout / "ai/agents/models.json").read_text())
            for name in ("code-reviewer", "debugger", "codebase-explorer"):
                source = (checkout / "ai/agents" / f"{name}.md").read_text().split("---", 2)[2].strip()
                for provider, directory in (("claude", "claude"), ("codex", "codex"),
                                            ("antigravity", "agy"), ("zcode", "zcode")):
                    suffix = ".toml" if provider == "codex" else ".md"
                    artifact = homes[directory] / "agents" / (name + suffix)
                    self.assertTrue(artifact.is_file(), str(artifact))
                    content = artifact.read_text()
                    self.assertIn(source, content if provider != "codex" else tomllib.loads(content)["developer_instructions"])
                    if provider == "codex":
                        native = tomllib.loads(content)
                        self.assertEqual(native["sandbox_mode"], "read-only")
                        self.assertEqual(native["model"], settings[name][provider]["model"])
                        self.assertEqual(native["model_reasoning_effort"], settings[name][provider]["effort"])
                    else:
                        self.assertIn("model: " + settings[name][provider]["model"], content)
            for name in ("review", "debug", "explore"):
                self.assertIn(f"name: {name}", (homes["codex"] / "skills" / name / "SKILL.md").read_text())
            self.assertTrue((homes["shared"] / "workflows/implementation.md").is_file())

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
