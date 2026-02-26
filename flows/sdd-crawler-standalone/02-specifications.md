# Specifications: Standalone Mode (Autonomous Engine)

**Version:** 0.3
**Status:** SPECIFICATIONS PHASE
**Last Updated:** 2026-01-30

---

## 1. Autonomous Loop
В режиме `--standalone` воркер работает по циклу:
1. `task = LPM.get_highest_priority_task()`
2. `result = Scraper.run(task)`
3. `LPM.save_result(result)` -> **Trigger Local Ripple Effect**.
4. Повторить.

## 2. Seed & Discovery
- **Seed**: Первоначальное наполнение из JSON/CSV.
- **Discovery**: Если парсер в процессе работы нашел новые ID (через `discovered_links`), они добавляются в ту же очередь. 
- Это превращает Standalone в саморазвивающуюся систему: дали один адрес -> он нашел владельца -> нашел другие его участки -> выкачал всё связанное.

## 3. CLI Commands
- `python main.py --standalone --seed initial.json`
- `python main.py --standalone --resume` (Продолжить с самого высокого приоритета)
- `python main.py --standalone --sync` (Выгрузить накопленное в Gateway)