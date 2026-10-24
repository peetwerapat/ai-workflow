#!/usr/bin/env python3
"""Deterministic context discovery, spec validation, and feature indexing (stdlib only)."""
import argparse
from collections import Counter
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import quote, unquote


STATUSES = ("🔴", "🚧", "📋", "⚠️", "✅", "❌", "📦")
TERMINAL = {"✅", "❌", "📦"}
TASK = re.compile(r"TASK-\d{8}-\d{4}")


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".workflow-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def resolve(start):
    start = Path(start).resolve()
    if start.is_file():
        start = start.parent
    root = start
    for directory in (start, *start.parents):
        if (directory / ".git").exists() or (directory / ".ai/context").is_dir():
            root = directory
            break
    shared = next((p for p in (root, *root.parents)
                   if (p / ".ai/context/PROJECT.md").is_file()), None)
    memory = [str(root / name) for name in ("CLAUDE.md", "AGENTS.md", "GEMINI.md")
              if (root / name).is_file()]
    return {"root": str(root), "shared": str(shared) if shared else None,
            "memory": memory, "context": str(root / ".ai/context")}


def section(raw, title):
    match = re.search(r"^## " + re.escape(title) + r"\s*\n(.*?)(?=^## |\Z)", raw, re.M | re.S)
    return match.group(1) if match else ""


def overall(values):
    values = set(values)
    if "🔴" in values:
        return "🔴"
    if "🚧" in values or ("📋" in values and values & {"✅", "⚠️"}):
        return "🚧"
    if values == {"📋"}:
        return "📋"
    if values == {"✅"}:
        return "✅"
    if values <= {"✅", "⚠️"} and "⚠️" in values:
        return "⚠️"
    raise ValueError("Invalid per-repository status combination")


@dataclass
class Spec:
    path: Path
    task: str
    title: str
    metadata: dict
    status: str
    repos: dict
    raw: str


def parse(path):
    raw = path.read_text(encoding="utf-8")
    expected = TASK.fullmatch(path.stem.removeprefix("CLOSED-"))
    heading = re.search(r"^# (TASK-\d{8}-\d{4})\s*[—–-]\s*(.+)$", raw, re.M)
    if not expected or not heading or expected.group() != heading[1]:
        raise ValueError(f"{path}: filename and heading must contain the same Task ID")
    header = raw.split("\n## ", 1)[0]
    metadata = dict(re.findall(r"^\*\*([^*\n]+)\*\*:\s*([^\n]+)$", header, re.M))
    status = next((s for s in STATUSES if metadata.get("Status", "").startswith(s)), None)
    if not status or not metadata.get("Module"):
        # Cross-repository specs use a synthetic group if no module is declared.
        if not status or metadata.get("Scope") != "cross-repo":
            raise ValueError(f"{path}: missing/invalid Status or Module")
    repos = {}
    if metadata.get("Scope") == "cross-repo":
        names = [n.strip().strip("`") for n in metadata.get("Repos", "").split(",") if n.strip()]
        if not names or len(names) != len(set(names)):
            raise ValueError(f"{path}: missing/duplicate Repos")
        for line in section(raw, "Implementation Status").splitlines():
            cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0] in names:
                if cells[0] in repos:
                    raise ValueError(f"{path}: duplicate repository row {cells[0]}")
                repos[cells[0]] = next((s for s in STATUSES if cells[1].startswith(s)), "")
        if set(repos) != set(names) or any(s not in STATUSES[:5] for s in repos.values()):
            raise ValueError(f"{path}: Implementation Status must contain one valid row per repo")
        if status not in {"❌", "📦"}:
            status = overall(repos.values())
    return Spec(path, heading[1], heading[2], metadata, status, repos, raw)


def scan(context):
    specs, errors, seen = [], [], set()
    for path in sorted((context / "specs").glob("*.md")):
        if path.name == "README.md":
            continue
        try:
            spec = parse(path)
            if path.name.startswith("CLOSED-") and spec.status not in TERMINAL:
                raise ValueError(f"{path}: nonterminal spec has CLOSED prefix; reopen through /change")
            if spec.task in seen:
                raise ValueError(f"{path}: duplicate Task ID {spec.task}")
            seen.add(spec.task)
            specs.append(spec)
        except ValueError as error:
            errors.append(str(error))
    return specs, errors


def validate(root):
    resolved = resolve(root)
    contexts = [Path(resolved["context"])]
    if resolved["shared"] and resolved["shared"] != resolved["root"]:
        contexts.append(Path(resolved["shared"]) / ".ai/context")
    errors, warnings, tasks = [], [], set()
    for context in contexts:
        specs, failures = scan(context)
        errors.extend(failures)
        for spec in specs:
            if spec.task in tasks:
                errors.append(f"{spec.path}: Task ID also exists in another context")
            tasks.add(spec.task)
            declared = spec.metadata["Status"]
            if not declared.startswith(spec.status):
                errors.append(f"{spec.path}: overall Status must be {spec.status}")
            if spec.path.name.startswith("CLOSED-") and spec.status not in TERMINAL:
                errors.append(f"{spec.path}: nonterminal spec has CLOSED prefix; reopen through /change")
            if spec.status == "✅" and not section(spec.raw, "Implementation Status").strip():
                errors.append(f"{spec.path}: Done requires Implementation Status and test evidence")
            if spec.status == "✅" and not re.search(r"\bpassed\b", section(spec.raw, "Implementation Status") + section(spec.raw, "Validation Evidence"), re.I):
                warnings.append(f"{spec.path}: no explicit passing test evidence; metadata alone cannot verify Done")
            # Only local Markdown links are checked; API routes and remote URLs are not file links.
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", spec.raw):
                target = unquote(target.strip("<>").split("#", 1)[0])
                if target and ":" not in target and not target.startswith("/"):
                    if not (spec.path.parent / target).exists():
                        errors.append(f"{spec.path}: broken link {target}")
        if not (context / "specs").is_dir():
            warnings.append(f"{context}: no specs directory; direct coding is allowed")
    return {"errors": errors, "warnings": warnings, "tasks": len(tasks)}


def reindex(root, dry_run=False):
    resolved = resolve(root)
    context = Path(resolved["context"])
    specs, errors = scan(context)
    external = []
    if resolved["shared"] and resolved["shared"] != resolved["root"]:
        shared_specs, failures = scan(Path(resolved["shared"]) / ".ai/context")
        errors.extend(failures)
        external = [s for s in shared_specs if Path(resolved["root"]).name in s.repos]
    ids = [s.task for s in specs + external]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate Task ID across repository and shared context")
    if errors:
        raise ValueError("\n".join(errors))
    lines = ["# Feature Registry", "", "> Derived view — regenerated by `/reindex`.",
             "> Source of truth: local specs and relevant shared project specs.", "", "## Legend", "",
             "| Icon | Status |", "|---|---|"]
    names = ("Blocked", "In Progress", "Planned", "Done (untested)", "Done", "Cancelled", "Deprecated")
    lines.extend(f"| {icon} | {name} |" for icon, name in zip(STATUSES, names))
    entries, renames, warnings = [], [], []
    for spec in specs + external:
        is_external = spec in external
        status = spec.repos[Path(resolved["root"]).name] if is_external and spec.status not in {"❌", "📦"} else spec.status
        path = spec.path
        if not is_external and spec.status in TERMINAL and not path.name.startswith("CLOSED-"):
            path = path.with_name("CLOSED-" + path.name)
            if path.exists():
                raise ValueError(f"Refusing to overwrite {path}")
            renames.append((spec.path, path))
        if not spec.metadata["Status"].startswith(spec.status):
            warnings.append(f"{spec.task}: declared Status differs from computed {spec.status}; /change must update it")
        module = "Cross-repo" if is_external else spec.metadata.get("Module", "Cross-repo")
        if status in {"❌", "📦"}:
            module = "Archived"
        link = quote(os.path.relpath(path, context).replace(os.sep, "/"), safe="/.-_")
        updated = spec.metadata.get("Last Updated", spec.metadata.get("Created", "unknown"))
        developer = spec.metadata.get("Created", "unknown").partition(" by ")[2] or "unknown"
        closed = " 🔒" if path.name.startswith("CLOSED-") else ""
        history = section(spec.raw, "Changelog").split("BUILT", 1)
        revisions = len(re.findall(r"\b(?:CHANGED|FIXED|REFACTORED)\b", history[1])) if len(history) > 1 else 0
        badge = f" ✏️({revisions})" if revisions else ""
        detail = " · ".join(f"{repo} {state}" for repo, state in spec.repos.items())
        entry = f"- {status}{closed}{badge} [{spec.task}]({link}) — {spec.title} ({developer}) — updated {updated}"
        if detail:
            entry += f" — overall {spec.status} · {detail}"
        entries.append((module, status, spec.task, entry))
    counts = Counter(e[1] for e in entries)
    lines += ["", "## At a Glance", "", f"**Total**: {len(entries)} | " + " | ".join(f"{s} {counts[s]}" for s in STATUSES),
              "", "| Module | 📋 | 🚧 | ⚠️ | ✅ | 🔴 |", "|---|---|---|---|---|---|"]
    for module in sorted({e[0] for e in entries}):
        count = Counter(e[1] for e in entries if e[0] == module)
        lines.append(f"| {module} | " + " | ".join(str(count[s]) for s in ("📋", "🚧", "⚠️", "✅", "🔴")) + " |")
    for module in sorted({e[0] for e in entries}):
        lines += ["", f"# {module}", ""]
        lines.extend(e[3] for e in sorted(entries, key=lambda e: (STATUSES.index(e[1]), e[2])) if e[0] == module)
    content = "\n".join(lines) + "\n"
    if not dry_run:
        # Do not stage git changes or alter spec contents. Renames are reversible.
        completed = []
        try:
            for source, destination in renames:
                source.rename(destination)
                completed.append((source, destination))
            atomic_write(context / "features.md", content)
        except OSError:
            for source, destination in reversed(completed):
                destination.rename(source)
            raise
    return {"index": str(context / "features.md"), "tasks": len(entries),
            "renames": [[str(a), str(b)] for a, b in renames], "warnings": warnings,
            "dry_run": dry_run}


def context_plan(root, paths):
    resolved = resolve(root)
    context = Path(resolved["context"])
    required = []
    if resolved["shared"]:
        required.append(str(Path(resolved["shared"]) / ".ai/context/PROJECT.md"))
    required += resolved["memory"]
    required += [str(context / name) for name in ("MEMORY.md", "ARCHITECTURE.md", "context-map.json")
                 if (context / name).is_file()]
    selected, stale = [], []
    map_file = context / "context-map.json"
    if map_file.is_file():
        mapping = json.loads(map_file.read_text())
        if mapping.get("version") != 1 or not isinstance(mapping.get("modules"), list):
            raise ValueError("Context map requires version 1 and a modules list")
        for rule in mapping.get("modules", []):
            prefix = rule["path"].rstrip("/")
            if not prefix or Path(prefix).is_absolute() or ".." in Path(prefix).parts:
                raise ValueError(f"Invalid module prefix: {prefix}")
            if not any(p == prefix or p.startswith(prefix + "/") for p in paths):
                continue
            for name in rule.get("context", []):
                target = (Path(resolved["root"]) / name).resolve()
                if not target.is_relative_to(Path(resolved["root"])):
                    raise ValueError(f"Context map escapes repository: {name}")
                (selected if target.is_file() else stale).append(str(target))
    return {**resolved, "required": list(dict.fromkeys(required)),
            "selected": list(dict.fromkeys(selected)), "missing": stale,
            "continuity": [str(context / name) for name in ("HANDOFF.md", "LESSONS.md") if (context / name).is_file()],
            "note": "Candidate paths only; verify evidence and load relevant shared context from PROJECT.md."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("resolve", "context", "validate", "reindex"))
    parser.add_argument("--root", default=".")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Compatibility flag; all metadata is always read")
    args = parser.parse_args()
    try:
        if args.command == "resolve":
            result = resolve(args.root)
        elif args.command == "context":
            result = context_plan(args.root, args.path)
        elif args.command == "validate":
            result = validate(args.root)
        else:
            result = reindex(args.root, args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(bool(result.get("errors")))
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"errors": [str(error)]}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
