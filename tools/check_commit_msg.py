#!/usr/bin/env python3
"""
Validates commit messages according to Terrarich Horizon commit rules:
- Must follow Conventional Commits: <type>(<scope>): <clear description>
- Must not be a vague/WIP commit
- Must be descriptive (at least 10 characters)
"""

import re
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


ALLOWED_TYPES = (
    "feat",
    "fix",
    "perf",
    "refactor",
    "docs",
    "test",
    "chore",
    "style",
    "ci",
    "build",
)

BANNED_TITLES = {
    "wip",
    "work in progress",
    "temp",
    "temporary",
    "checkpoint",
    "fix",
    "bugfix",
    "fixes",
    "asdf",
    "test",
    "testing",
    "typo",
    "fix typo",
    "update",
    "changes",
}

COMMIT_PATTERN = re.compile(
    r"^(" + "|".join(ALLOWED_TYPES) + r")(\([a-zA-Z0-9_\-\./]+\))?(!)?:\s+(.+)$",
    re.IGNORECASE,
)


def validate_commit_message(msg: str) -> tuple[bool, str]:
    lines = [line.strip() for line in msg.strip().splitlines() if line.strip() and not line.strip().startswith("#")]
    if not lines:
        return False, "Сообщение коммита не может быть пустым."

    title = lines[0]

    # Allow automated Git actions (merges, reverts, tags)
    if title.startswith(("Merge branch", "Merge remote", "Merge pull request", "Revert \"")):
        return True, ""

    if len(title) < 10:
        return False, f"Заголовок коммита слишком короткий ({len(title)} симв.). Минимальная длина: 10 символов."

    clean_lower = title.lower().strip()
    if clean_lower in BANNED_TITLES:
        return False, f"Название коммита '{title}' запрещено. Коммиты должны описывать завершённую функцию."

    match = COMMIT_PATTERN.match(title)
    if not match:
        types_str = ", ".join(ALLOWED_TYPES)
        return False, (
            f"Заголовок коммита '{title}' не соответствует стандарту Conventional Commits.\n"
            f"Ожидаемый формат: <тип>(<область>): <понятное описание>\n"
            f"Допустимые типы: {types_str}\n"
            f"Примеры:\n"
            f"  feat(renderer): добавлена поддержка динамического освещения\n"
            f"  fix(worldgen): устранена ошибка при генерации пещер\n"
            f"  chore(release): подготовка версии v0.1.0"
        )

    description = match.group(4).strip()
    if len(description) < 5:
        return False, "Описание изменений в коммите слишком короткое."

    return True, ""


def main():
    if len(sys.argv) < 2:
        print("Использование: check_commit_msg.py <путь к файлу сообщения коммита>", file=sys.stderr)
        sys.exit(1)

    commit_msg_file = sys.argv[1]
    try:
        with open(commit_msg_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Ошибка чтения файла сообщения коммита: {e}", file=sys.stderr)
        sys.exit(1)

    ok, reason = validate_commit_message(content)
    if not ok:
        print("\n" + "=" * 60, file=sys.stderr)
        print(" ОШИБКА ВАЛИДАЦИИ КОММИТА (Правила форка Terrarich):", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(reason, file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
