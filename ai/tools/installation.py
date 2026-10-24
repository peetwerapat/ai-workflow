#!/usr/bin/env python3
"""Validate, diagnose, and transact ai-agent installations without dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
from workflow import atomic_write


def settings():
    home = Path.home()
    return {name: Path(os.environ.get(variable, str(default))).absolute()
            for name, variable, default in (
                ("store", "AI_AGENT_HOME", home / ".ai-agent"),
                ("shared", "AI_HOME", home / ".ai"),
                ("claude", "CLAUDE_HOME", home / ".claude"),
                ("codex", "CODEX_HOME", home / ".codex"),
                ("antigravity", "AGY_HOME", home / ".gemini/config"),
                ("zcode", "ZCODE_HOME", home / ".zcode"))}


def source_errors(root):
    errors = []
    try:
        models = json.loads((root / "ai/agents/models.json").read_text())
        for source in sorted((root / "ai/agents").glob("*.md")):
            text = source.read_text()
            for field in ("name", "description"):
                if not re.search(r"^" + field + r": .+", text, re.M):
                    errors.append(f"{source}: missing {field}")
            for provider in ("claude", "codex", "antigravity", "zcode"):
                config = models[source.stem][provider]
                model, effort = config.get("model"), config.get("effort")
                if not isinstance(model, str) or not model.strip():
                    errors.append(f"{source.stem}/{provider}: missing model")
                allowed = {"claude": {"low", "medium", "high", "max"},
                           "codex": {"minimal", "low", "medium", "high", "xhigh", "max", "ultra"},
                           "antigravity": set(), "zcode": {"low", "medium", "high"}}
                if effort is not None and effort not in allowed[provider]:
                    errors.append(f"{source.stem}/{provider}: unsupported effort {effort}")
                if provider in {"antigravity", "zcode"} and effort and model == "inherit":
                    errors.append(f"{source.stem}/{provider}: effort requires an explicit model")
                if provider == "antigravity" and model not in {"inherit", "flash", "pro"}:
                    errors.append(f"{source.stem}/{provider}: unsupported model tier")
        for source in sorted((root / "ai/commands").glob("*.md")):
            if not re.match(r"---\n.*?description: .+?\n.*?---\n", source.read_text(), re.S):
                errors.append(f"{source}: missing command frontmatter")
        if not (root / "ai/AI.md").is_file():
            errors.append("Missing ai/AI.md")
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(str(error))
    return errors


def fingerprint(path):
    if path.is_symlink():
        return {"link": os.readlink(path)}
    if not path.exists():
        return None
    if path.is_file():
        return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "mode": path.stat().st_mode & 0o777}
    return {str(p.relative_to(path)): fingerprint(p) for p in sorted(path.rglob("*"))
            if "__pycache__" not in p.parts and (not p.is_dir() or p.is_symlink())}


def targets(root, homes):
    result = [homes["shared"], root / ".install-prefs"]
    result += [homes["store"] / name for name in ("ai", "install.sh", "README.md", ".source", ".install-prefs", ".manifest.json")]
    commands = [p.stem for p in (root / "ai/commands").glob("*.md")]
    agents = [p.stem for p in (root / "ai/agents").glob("*.md")]
    for provider in ("claude", "codex", "antigravity", "zcode"):
        base = homes[provider]
        if provider != "antigravity":
            result.append(base / ("CLAUDE.md" if provider == "claude" else "AGENTS.md"))
        for name in commands:
            result.append(base / "skills" / name if provider in {"codex", "antigravity"}
                          else base / "commands" / f"{name}.md")
        result += [base / "agents" / (name + (".toml" if provider == "codex" else ".md")) for name in agents]
    result += list((homes["codex"] / "prompts").glob("*.md"))
    if not os.environ.get("AI_AGENT_NO_SHELL"):
        shell = Path(os.environ.get("SHELL", "")).name
        rc = {"zsh": ".zshrc", "bash": ".bashrc"}.get(shell)
        if shell == "bash" and (Path.home() / ".bash_profile").is_file():
            rc = ".bash_profile"
        if rc:
            result.append(Path.home() / rc)
    # Never snapshot nested paths twice; preserve symlinks as symlinks.
    result = sorted(set(result), key=lambda p: (len(p.parts), str(p)))
    unique = []
    for path in result:
        if not any(path.is_relative_to(parent) for parent in unique):
            unique.append(path)
    return unique


def history_path(store):
    return store.parent / ("." + store.name.lstrip(".") + "-history")


def copy_path(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        destination.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination)


def remove_path(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def restore(snapshot, check=False):
    data = json.loads((snapshot / "snapshot.json").read_text())
    entries = [(index, entry) for index, entry in enumerate(data["entries"])
               if "after" not in entry or entry["before"] != entry["after"]]
    for index, entry in entries:
        if entry["before"] is not None and fingerprint(snapshot / str(index)) != entry["before"]:
            raise ValueError(f"Snapshot is missing or corrupted: {snapshot / str(index)}; no files restored")
    if check:
        changed = [entry["path"] for _, entry in entries
                   if fingerprint(Path(entry["path"])) != entry.get("after")]
        if changed:
            raise ValueError("Files changed since installation; review before rollback: " + ", ".join(changed))
    for index, entry in reversed(entries):
        path = Path(entry["path"])
        remove_path(path)
        if entry["before"] is not None:
            copy_path(snapshot / str(index), path)


def manifest(root, homes, providers):
    target = homes["store"] / ".manifest.json"
    previous = json.loads(target.read_text()) if target.is_file() else {"targets": {}, "providers": {}}
    for path in targets(root, homes):
        # Track provider artifacts, not preferences, backups, source tree, or shell contents.
        if (path == homes["shared"] and providers) or any(path.is_relative_to(homes[p]) for p in providers):
            if path.exists() or path.is_symlink():
                previous["targets"][str(path)] = fingerprint(path)
    for provider in providers:
        previous["providers"][provider] = fingerprint(root / "ai")
    previous["source_root"] = str(root)
    atomic_write(target, json.dumps(previous, ensure_ascii=False, indent=2) + "\n")


def transact(root, arguments):
    failures = source_errors(root)
    if failures:
        raise ValueError("Source validation failed:\n" + "\n".join(failures))
    homes = settings()
    history = history_path(homes["store"])
    history.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = history / "lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError(f"Another installation may be running; inspect {lock} before retrying")
    try:
        snapshot = Path(tempfile.mkdtemp(prefix="release-", dir=history))
        paths = targets(root, homes)
        entries = []
        for index, path in enumerate(paths):
            before = fingerprint(path)
            entries.append({"path": str(path), "before": before})
            if before is not None:
                copy_path(path, snapshot / str(index))
        data = {"created": time.time(), "entries": entries}
        atomic_write(snapshot / "snapshot.json", json.dumps(data, indent=2) + "\n")
        environment = os.environ.copy()
        environment["AI_AGENT_TRANSACTION"] = "1"
        try:
            result = subprocess.run(["bash", str(root / "install.sh"), *arguments], env=environment)
            if result.returncode:
                restore(snapshot)
                print("ติดตั้งไม่สำเร็จ — คืนค่าไฟล์ก่อนติดตั้งแล้ว", file=sys.stderr)
                return result.returncode
            for entry in entries:
                entry["after"] = fingerprint(Path(entry["path"]))
            if all(entry["before"] == entry["after"] for entry in entries):
                return 0
            atomic_write(snapshot / "snapshot.json", json.dumps(data, indent=2) + "\n")
            atomic_write(history / "latest", str(snapshot) + "\n")
            print(f"Snapshot: {snapshot} (ย้อนกลับด้วย --rollback)")
            return 0
        except BaseException:
            restore(snapshot)
            raise
    finally:
        lock.rmdir()


def doctor(root, providers=()):
    homes = settings()
    errors, warnings = source_errors(root), []
    target = homes["store"] / ".manifest.json"
    if not target.is_file():
        errors.append("No installation manifest; run install.sh <provider> first")
    else:
        data = json.loads(target.read_text())
        for name, expected in data["targets"].items():
            path = Path(name)
            if providers and path != homes["shared"] and not any(path.is_relative_to(homes[p]) for p in providers):
                continue
            if fingerprint(path) != expected:
                errors.append(f"Missing/modified artifact: {path}; reinstall its provider")
            if path.is_symlink() and not path.exists():
                errors.append(f"Broken symlink: {path}; reinstall its provider")
        for provider in providers or data["providers"]:
            if fingerprint(root / "ai") != data["providers"].get(provider):
                errors.append(f"Source changed or {provider} not installed; reinstall {provider}")
    for executable in ("claude", "codex", "agy"):
        if not shutil.which(executable):
            warnings.append(f"{executable} not found in PATH (only needed when using that assistant)")
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "history": str(history_path(homes["store"])),
            "note": "Checks local files and generation drift; does not verify remote model availability or runtime schema compatibility."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate-source", "doctor", "transaction", "rollback", "record"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--provider", action="append", choices=("claude", "codex", "antigravity", "zcode"), default=[])
    args, remaining = parser.parse_known_args()
    try:
        if args.command == "transaction":
            return transact(args.root, remaining[1:] if remaining[:1] == ["--"] else remaining)
        if args.command == "record":
            manifest(args.root, settings(), args.provider)
            return 0
        if args.command == "rollback":
            history = history_path(settings()["store"])
            latest = history / "latest"
            snapshot = Path(latest.read_text().strip())
            if snapshot.parent != history:
                raise ValueError("Invalid rollback snapshot")
            lock = history / "lock"
            lock.mkdir()
            try:
                restore(snapshot, check=True)
                latest.unlink()
            finally:
                lock.rmdir()
            print("คืนค่าก่อนการติดตั้งครั้งล่าสุดแล้ว")
            return 0
        result = doctor(args.root, args.provider) if args.command == "doctor" else {"errors": source_errors(args.root)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(bool(result["errors"]))
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
