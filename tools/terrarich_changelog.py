#!/usr/bin/env python3
"""
tools/terrarich_changelog.py
Changelog & GitHub Release Notes generator for Horizon (Fork by Terrarich).

Usage:
  python tools/terrarich_changelog.py                  # Show changelog from git log
  python tools/terrarich_changelog.py --notes          # Generate RELEASE_NOTES.md
  python tools/terrarich_changelog.py --bump v0.2.0    # Update CHANGELOG.md for new release
"""

import argparse
from datetime import date
from pathlib import Path
import re
import subprocess
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"

CATEGORY_MAP = {
    "feat": ("✨ Новые функции", "Features"),
    "fix": ("🐛 Исправления ошибок", "Bug Fixes"),
    "perf": ("⚡ Производительность", "Performance Improvements"),
    "refactor": ("🔄 Рефакторинг", "Refactoring"),
    "docs": ("📚 Документация", "Documentation"),
    "test": ("🧪 Тестирование", "Tests"),
    "chore": ("⚙️ Обслуживание", "Maintenance"),
    "style": ("🎨 Стилистика", "Code Style"),
    "ci": ("🚀 CI/CD", "Continuous Integration"),
    "build": ("📦 Сборка", "Build System"),
}

COMMIT_RE = re.compile(
    r"^([0-9a-f]+)\s+((feat|fix|perf|refactor|docs|test|chore|style|ci|build)(\([^)]+\))?!?:?\s*(.+))$",
    re.IGNORECASE,
)


def get_latest_tag() -> str | None:
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        ).decode("utf-8").strip()
        return tag
    except subprocess.CalledProcessError:
        return None


def get_commits_since(ref: str | None = None) -> list[tuple[str, str, str, str]]:
    """Returns list of (hash, type, scope, description)."""
    rev_range = f"{ref}..HEAD" if ref else "HEAD"
    try:
        log_out = subprocess.check_output(
            ["git", "log", "--oneline", "--no-merges", rev_range],
            cwd=REPO_ROOT,
        ).decode("utf-8", errors="replace").strip()
    except subprocess.CalledProcessError:
        return []

    if not log_out:
        return []

    results = []
    for line in log_out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            continue
        commit_hash, full_msg = parts[0], parts[1]

        m = re.match(r"^([a-zA-Z]+)(?:\(([^)]+)\))?!?:?\s*(.*)$", full_msg)
        if m:
            ctype = m.group(1).lower()
            scope = m.group(2) or ""
            desc = m.group(3).strip()
            results.append((commit_hash, ctype, scope, desc))
        else:
            results.append((commit_hash, "chore", "", full_msg))
    return results


def format_markdown_sections(commits: list[tuple[str, str, str, str]]) -> str:
    grouped: dict[str, list[str]] = {}
    for commit_hash, ctype, scope, desc in commits:
        cat_key = ctype if ctype in CATEGORY_MAP else "chore"
        scope_prefix = f"**{scope}**: " if scope else ""
        entry = f"- {scope_prefix}{desc} (`{commit_hash[:7]}`)"
        grouped.setdefault(cat_key, []).append(entry)

    if not grouped:
        return "- Нет новых коммитов в этом диапазоне.\n"

    lines = []
    # Preferred order
    order = ["feat", "fix", "perf", "refactor", "docs", "test", "chore"]
    for k in order:
        if k in grouped:
            cat_title = CATEGORY_MAP[k][0]
            lines.append(f"### {cat_title}")
            lines.extend(grouped[k])
            lines.append("")

    for k, entries in grouped.items():
        if k not in order:
            cat_title = CATEGORY_MAP.get(k, (k.capitalize(), ""))[0]
            lines.append(f"### {cat_title}")
            lines.extend(entries)
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def generate_release_notes(version: str, commits: list[tuple[str, str, str, str]]) -> str:
    content = format_markdown_sections(commits)
    notes = f"""# Релиз {version} — Horizon (Fork by Terrarich)

**Автор форка:** Terrarich  
**Дата выпуска:** {date.today().isoformat()}

---

{content}

---
*Собрано с соблюдением всех лицензий и правил проекта Horizon.*
"""
    return notes


def bump_changelog(version: str, notes_content: str):
    if not CHANGELOG_PATH.exists():
        print(f"Файл {CHANGELOG_PATH} не найден!", file=sys.stderr)
        return False

    text = CHANGELOG_PATH.read_text(encoding="utf-8")
    today = date.today().isoformat()
    new_release_header = f"## [{version}] — {today}\n\n{notes_content.strip()}\n"

    # Replace Unreleased section or prepend
    if "## [Unreleased]" in text:
        unreleased_replacement = f"## [Unreleased] — В разработке\n\n### ✨ Новые функции\n- Ожидаются новые завершённые функции форка.\n\n---\n\n{new_release_header}\n---"
        updated = re.sub(
            r"## \[Unreleased\].*?(?=\n## \[|\Z)",
            unreleased_replacement,
            text,
            count=1,
            flags=re.DOTALL,
        )
    else:
        updated = f"{new_release_header}\n---\n\n{text}"

    CHANGELOG_PATH.write_text(updated, encoding="utf-8")
    print(f"CHANGELOG.md успешно обновлён для версии {version}!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Утилита генерации ченджлогов для Terrarich Horizon")
    parser.add_argument("--since", help="Git ref (тег или коммит), начиная с которого собирать лог")
    parser.add_argument("--version", default="v0.1.0", help="Версия для описания релиза")
    parser.add_argument("--notes", action="store_true", help="Сохранить готовый RELEASE_NOTES.md для GitHub")
    parser.add_argument("--bump", metavar="VERSION", help="Обновить CHANGELOG.md и перенести Unreleased в указанную версию")
    args = parser.parse_args()

    since_ref = args.since or get_latest_tag()
    commits = get_commits_since(since_ref)

    if args.bump:
        notes_body = format_markdown_sections(commits)
        bump_changelog(args.bump, notes_body)
        return

    notes = generate_release_notes(args.version, commits)

    if args.notes:
        out_file = REPO_ROOT / f"RELEASE_NOTES_{args.version}.md"
        out_file.write_text(notes, encoding="utf-8")
        print(f"Файл заметок к релизу успешно создан: {out_file}")
    else:
        print(notes)


if __name__ == "__main__":
    main()
