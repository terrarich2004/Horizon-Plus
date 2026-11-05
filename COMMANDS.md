# ⚡ Шпаргалка команд Horizon (Fork by Terrarich)

Краткий справочник всех основных команд для сборки, запуска, разработки и выпуска релизов.

---

## 1. 📦 Подготовка ресурсов (Выполняется один раз)

Horizon не хранит защищённые авторским правом файлы Mojang в Git. Ресурсы генерируются локально из официального Minecraft 26.3:

| Команда | Для чего |
|---|---|
| `cargo run --release -p horizon-prepare -- --prepare --server-jar "C:\Path\server.jar"` | Распаковать и собрать ресурсы из скачанного `server.jar`. |
| `cargo run --release -p horizon-prepare -- sounds` | *(Опционально)* Извлечь звуки из локального клиента Minecraft. |

*Ресурсы будут сохранены в папку `.local/horizon-client/26.3`.*

---

## 2. 🔨 Сборка игры (Билд)

| Команда | Для чего |
|---|---|
| `cargo build --profile fast -p horizon-client` | **Быстрый билд** для разработки и игры (быстро линкуется). |
| `cargo build --release -p horizon-client` | **Релизный билд** с максимальной оптимизацией и наибольшим FPS. |
| `cargo check --workspace` | Быстрая проверка ошибок компиляции без сборки exe. |

*Собранные файлы находятся в: `target\fast\horizon-client.exe` или `target\release\horizon-client.exe`.*

---

## 3. 🎮 Запуск игры

| Команда | Для чего |
|---|---|
| `cd launcher; cargo run` | **Графический лаунчер** (аккаунты, миры, настройки в GUI). |
| `cargo run --profile fast -p horizon-client -- --resources .local/horizon-client/26.3 --world TestWorld` | **Прямой запуск клиента** с указанием мира. |
| `.\target\fast\horizon-client.exe --resources .local/horizon-client/26.3 --world TestWorld` | Быстрый запуск уже скомпилированного `.exe`. |
| `cargo run --profile fast -p horizon-client -- --dedicated --world ServerWorld` | Запуск **выделенного сервера** (без окна и графики). |

### Полезные флаги запуска:
* `--creative` — открыть мир в творческом режиме.
* `--seed 12345` — сид генерации нового мира.
* `--offscreen` — запуск без открытия окна (для автоматических тестов).

---

## 4. 📝 Коммиты (По правилам Terrarich)

Каждый коммит должен быть **завершённой функцией** с понятным названием по стандарту Conventional Commits:

| Команда | Для чего |
|---|---|
| `git status` | Проверить изменённые файлы. |
| `git add .` | Добавить файлы в индекс. |
| `git commit -m "feat(renderer): описание готовой функции"` | Создать коммит с новой возможностью (`feat`). |
| `git commit -m "fix(worldgen): описание исправленной ошибки"` | Создать коммит с исправлением бага (`fix`). |
| `git commit -m "perf(chunks): описание оптимизации"` | Создать коммит с оптимизацией скорости (`perf`). |
| `python tools/check_public_tree.py` | Проверить, что случайно не добавлены файлы Mojang. |

*Если название коммита непонятное (например, "wip" или "fix"), хук `.githooks/commit-msg` отклонит его.*

---

## 5. 🚀 Ченджлог и публикация релиза

Релизы публикуются **только по вашей явной команде**:

| Команда | Для чего |
|---|---|
| `python tools/terrarich_changelog.py` | Посмотреть список новых функций с прошлого релиза. |
| `python tools/terrarich_release.py --version v0.1.0 --dry-run` | **Безопасный тест:** посмотреть, как соберётся релиз, без изменений в Git. |
| `python tools/terrarich_release.py --version v0.1.0` | **Выпустить релиз:** проверит код, обновит `CHANGELOG.md`, создаст коммит и Git-тег. |
| `.\tools\terrarich_release.ps1 -Version v0.1.0` | То же самое через удобный PowerShell скрипт. |
| `git push origin main --tags` | Отправить коммиты и релизный тег на GitHub. |

---

## 6. 🧪 Тесты и проверки качества

| Команда | Для чего |
|---|---|
| `python tools/pr_ready.py --quick` | Экспресс-проверка: форматирование `fmt`, линтер `clippy`, тесты. |
| `cargo test -p horizon-client -p horizon-client-lib --lib --bins --tests` | Запуск unit- и интеграционных тестов клиента. |
