import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai/tools"))
import workflow


def write_spec(root, task="TASK-20261001-0900", status="📋 Planned", cross=None, closed=False):
    context = root / ".ai/context"
    path = context / "specs" / (("CLOSED-" if closed else "") + task + ".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "**Module**: customers\n"
    implementation = "Pending /build"
    if cross:
        header += "**Scope**: cross-repo\n**Repos**: " + ", ".join(cross) + "\n"
        implementation = "| Repo | Status | Files | Tests |\n|---|---|---|---|\n" + "\n".join(
            f"| {repo} | {state} | {repo}/app.py | python3 -m unittest: passed |" for repo, state in cross.items())
    path.write_text(f"# {task} — Customer tags\n\n{header}**Status**: {status}\n"
                    "**Created**: 2026-10-01 by Dev\n**Last Updated**: 2026-10-02 by Dev\n\n"
                    f"## Business Rules\n\nTags must be unique.\n\n## Implementation Status\n\n{implementation}\n\n"
                    "## Changelog\n\n- **2026-10-01** ADDED — Initial spec\n")
    return path


class WorkflowTest(unittest.TestCase):
    def test_resolve_nested_repo_and_shared_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".ai/context").mkdir(parents=True)
            (root / ".ai/context/PROJECT.md").write_text("# Shared")
            repo = root / "api"
            (repo / ".git").mkdir(parents=True)
            nested = repo / "src/customers"
            nested.mkdir(parents=True)
            result = workflow.resolve(nested)
            self.assertEqual(Path(result["root"]), repo.resolve())
            self.assertEqual(Path(result["shared"]), root.resolve())

    def test_reindex_is_idempotent_and_preserves_spec_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = write_spec(root, status="✅ Done")
            original = path.read_text()
            result = workflow.reindex(root)
            self.assertEqual(len(result["renames"]), 1)
            closed = path.with_name("CLOSED-" + path.name)
            self.assertEqual(closed.read_text(), original)
            index = root / ".ai/context/features.md"
            before = index.read_bytes()
            workflow.reindex(root)
            self.assertEqual(index.read_bytes(), before)
            self.assertIn("specs/CLOSED-TASK-20261001-0900.md", before.decode())

    def test_duplicate_prevents_any_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            active = write_spec(root, status="✅ Done")
            write_spec(root, closed=True, status="✅ Done")
            index = root / ".ai/context/features.md"
            index.write_text("keep this index")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                workflow.reindex(root)
            self.assertTrue(active.exists())
            self.assertEqual(index.read_text(), "keep this index")

    def test_cross_repo_uses_local_status_and_real_relative_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            shared = write_spec(project, status="🚧 In Progress", cross={"api": "✅", "web": "📋"})
            (project / ".ai/context/PROJECT.md").write_text("# Project")
            repo = project / "api"
            (repo / ".git").mkdir(parents=True)
            workflow.reindex(repo)
            index = repo / ".ai/context/features.md"
            content = index.read_text()
            expected = os.path.relpath(shared, index.parent)
            self.assertIn(f"]({expected})", content)
            self.assertIn("- ✅ [TASK-", content)
            self.assertTrue(shared.exists())
            self.assertIn("overall 🚧", content)

    def test_dry_run_has_no_writes_and_closed_shared_is_included(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            shared = write_spec(project, status="✅ Done", cross={"api": "✅", "web": "✅"}, closed=True)
            (project / ".ai/context/PROJECT.md").write_text("# Project")
            repo = project / "api"
            (repo / ".git").mkdir(parents=True)
            result = workflow.reindex(repo, dry_run=True)
            self.assertEqual(result["tasks"], 1)
            self.assertFalse((repo / ".ai").exists())
            self.assertTrue(shared.exists())

    def test_status_aggregation_and_missing_rows(self):
        self.assertEqual(workflow.overall(["⚠️", "✅"]), "⚠️")
        self.assertEqual(workflow.overall(["📋", "⚠️"]), "🚧")
        self.assertEqual(workflow.overall(["🔴", "✅"]), "🔴")
        with tempfile.TemporaryDirectory() as temporary:
            path = write_spec(Path(temporary), cross={"api": "✅", "web": "📋"})
            path.write_text(path.read_text().replace("| web | 📋 | web/app.py | python3 -m unittest: passed |", ""))
            with self.assertRaisesRegex(ValueError, "one valid row"):
                workflow.parse(path)

    def test_validate_bad_id_status_and_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = write_spec(root)
            path.write_text(path.read_text() + "\n[missing](missing.md)\n")
            self.assertIn("broken link", " ".join(workflow.validate(root)["errors"]))
            path.write_text(path.read_text().replace("📋 Planned", "unknown"))
            self.assertTrue(workflow.validate(root)["errors"])
            path.write_text(path.read_text().replace("TASK-20261001-0900", "TASK-20261001-0910"))
            self.assertIn("same Task ID", " ".join(workflow.validate(root)["errors"]))

    def test_context_selects_only_affected_module(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            context = root / ".ai/context"
            context.mkdir(parents=True)
            (context / "customer.md").write_text("# Customer")
            (context / "context-map.json").write_text(json.dumps({"version": 1, "modules": [
                {"path": "src/customer", "context": [".ai/context/customer.md"]},
                {"path": "src/billing", "context": [".ai/context/billing.md"]}]}))
            result = workflow.context_plan(root, ["src/customer/handler.py"])
            self.assertEqual(result["selected"], [str(context.resolve() / "customer.md")])
            self.assertEqual(result["missing"], [])

    def test_non_git_context_is_found_from_subdirectory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".ai/context").mkdir(parents=True)
            nested = root / "src/customer"
            nested.mkdir(parents=True)
            self.assertEqual(workflow.resolve(nested)["root"], str(root.resolve()))

    def test_invalid_closed_spec_and_legacy_name_are_not_silently_indexed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            closed = write_spec(root, closed=True)
            with self.assertRaisesRegex(ValueError, "nonterminal"):
                workflow.reindex(root)
            closed.rename(closed.with_name("AUTH-001.md"))
            with self.assertRaisesRegex(ValueError, "Task ID"):
                workflow.reindex(root)

    def test_context_map_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            context = root / ".ai/context"
            context.mkdir(parents=True)
            (context / "context-map.json").write_text(json.dumps({"version": 1, "modules": [
                {"path": "src", "context": ["../outside.md"]}]}))
            with self.assertRaisesRegex(ValueError, "escapes repository"):
                workflow.context_plan(root, ["src/app.py"])


if __name__ == "__main__":
    unittest.main()
