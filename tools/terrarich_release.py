#!/usr/bin/env python3
"""
tools/terrarich_release.py
Interactive & safe release assistant for Horizon (Fork by Terrarich).

Usage:
  python tools/terrarich_release.py                       # Interactive mode
  python tools/terrarich_release.py --version v0.1.0      # Release specific version
  python tools/terrarich_release.py --version v0.1.0 --dry-run  # Dry-run preview
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
sys.path.insert(0, str(REPO_ROOT / "tools"))

try:
    from terrarich_changelog import (
        bump_changelog,
        format_markdown_sections,
        generate_release_notes,
        get_commits_since,
        get_latest_tag,
    )
except ImportError:
    print("Ошибка импорта модуля terrarich_changelog.py", file=sys.stderr)
    sys.exit(1)


def run_cmd(cmd: list[str], check: bool = True) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if check and proc.returncode != 0:
        print(f"Ошибка при выполнении команды: {' '.join(cmd)}\n{proc.stdout}", file=sys.stderr)
        sys.exit(proc.returncode)
    return proc.returncode, proc.stdout.strip()


def check_git_author():
    _, author_name = run_cmd(["git", "config", "user.name"], check=False)
    if not author_name or "Terrarich" not in author_name:
        print("Внимание: Git user.name не установлен в 'Terrarich'!")
        print("Устанавливаю локально: git config user.name 'Terrarich'")
        run_cmd(["git", "config", "user.name", "Terrarich"])


def validate_version(ver: str) -> bool:
    # Matches vX.Y.Z, vX.Y.Z-beta, etc.
    return bool(re.match(r"^v?\d+\.\d+\.\d+(-[a-zA-Z0-9_\-\.]+)?$", ver.strip()))


def main():
    parser = argparse.ArgumentParser(description="Утилита выпуска релиза для Terrarich Horizon")
    parser.add_argument("--version", help="Версия релиза (например: v0.1.0, v1.0.0)")
    parser.add_argument("--dry-run", action="store_true", help="Предварительный просмотр без изменения репозитория")
    parser.add_argument("--skip-check", action="store_true", help="Пропустить проверку компиляции cargo check")
    parser.add_argument("--yes", "-y", action="store_true", help="Автоматическое подтверждение всех шагов")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print(" 🚀 СИСТЕМА ПУБЛИКАЦИИ РЕЛИЗОВ HORIZON (FORK BY TERRARICH)")
    print("=" * 65 + "\n")

    check_git_author()

    # Step 1: Version determination
    version = args.version
    if not version:
        latest = get_latest_tag() or "нет тегов (первый релиз)"
        print(f"Текущий последний тег: {latest}")
        try:
            version = input("Введите номер новой версии (например, v0.1.0): ").strip()
        except EOFError:
            version = "v0.1.0"

    if not version:
        print("Версия не указана. Выпуск отменён.")
        sys.exit(1)

    if not version.startswith("v"):
        version = f"v{version}"

    if not validate_version(version):
        print(f"Ошибка: Неверный формат версии '{version}'. Ожидается формат vX.Y.Z (например, v0.1.0).")
        sys.exit(1)

    print(f"\n[1/6] Подготовка релиза: {version}")
    print(f"      Автор релиза: Terrarich")
    print(f"      Дата: {date.today().isoformat()}")

    # Step 2: Working directory check
    print("\n[2/6] Проверка состояния Git репозитория...")
    code, status_out = run_cmd(["git", "status", "--porcelain"], check=False)
    if status_out:
        print("Обнаружены изменённые или неотслеживаемые файлы:")
        for line in status_out.splitlines()[:10]:
            print(f"  {line}")
        if not args.yes and not args.dry_run:
            ans = input("Продолжить и включить текущие изменения в релиз? (y/N): ").strip().lower()
            if ans != "y":
                print("Выпуск релиза отменён пользователем.")
                sys.exit(1)

    # Step 3: Fast build / syntax verification
    if not args.skip_check and not args.dry_run:
        print("\n[3/6] Проверка компиляции проекта (cargo check)...")
        print("      (Это гарантирует, что релиз рабочий и без синтаксических ошибок)")
        code, check_out = run_cmd(["cargo", "check", "-p", "horizon-core", "-p", "horizon-items"], check=False)
        if code != 0:
            print("Предупреждение: cargo check завершился с кодом ошибки.")
            if not args.yes:
                ans = input("Продолжить несмотря на предупреждения? (y/N): ").strip().lower()
                if ans != "y":
                    print("Выпуск релиза отменён.")
                    sys.exit(1)
        else:
            print("      ✓ Проверка компиляции успешно пройдена.")
    else:
        print("\n[3/6] Пропуск шага компиляции (флаг --skip-check или --dry-run).")

    # Step 4: Changelog and notes generation
    print("\n[4/6] Сбор списка изменений и формирование заметок к релизу...")
    since_ref = get_latest_tag()
    commits = get_commits_since(since_ref)
    notes_text = generate_release_notes(version, commits)
    notes_body = format_markdown_sections(commits)

    print("-" * 50)
    print(notes_text)
    print("-" * 50)

    if args.dry_run:
        print("\n[DRY RUN] Режим предварительного просмотра завершён. Никаких изменений в Git не внесено.")
        return

    if not args.yes:
        ans = input(f"Подтвердить выпуск релиза {version}? (y/N): ").strip().lower()
        if ans != "y":
            print("Выпуск отменён.")
            sys.exit(0)

    # Step 5: Update files and commit
    print("\n[5/6] Обновление CHANGELOG.md и фиксация релиза в Git...")
    bump_changelog(version, notes_body)

    release_notes_file = REPO_ROOT / f"RELEASE_NOTES_{version}.md"
    release_notes_file.write_text(notes_text, encoding="utf-8")
    print(f"      ✓ Заметки сохранены в {release_notes_file.name}")

    run_cmd(["git", "add", "CHANGELOG.md", f"RELEASE_NOTES_{version}.md", "RULES.md", "LICENSE"])
    commit_msg = f"chore(release): Terrarich release {version}"
    run_cmd(["git", "commit", "-m", commit_msg])
    print(f"      ✓ Создан релизный коммит: '{commit_msg}'")

    # Step 6: Create Tag
    print(f"\n[6/6] Создание Git-тега {version}...")
    run_cmd(["git", "tag", "-a", version, "-m", f"Release {version} by Terrarich"])
    print(f"      ✓ Создан тег: {version}")

    print("\n" + "=" * 65)
    print(f" 🎉 РЕЛИЗ {version} УСПЕШНО СФОРМИРОВАН ЛОКАЛЬНО!")
    print("=" * 65)
    print("\nДля публикации изменений и тега на GitHub выполните:")
    print(f"   git push origin main --tags\n")
    print("Для создания релиза на GitHub:")
    print(f"   1. Откройте страницу репозитория -> Releases -> Draft a new release")
    print(f"   2. Выберите тег {version}")
    print(f"   3. Скопируйте содержимое файла {release_notes_file.name}")
    print(f"   4. Нажмите 'Publish release'\n")


if __name__ == "__main__":
    main()
