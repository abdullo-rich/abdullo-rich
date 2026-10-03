"""Исправляет KeyError: 'pk' при скачивании актуального (highlights) в insta-dl 0.1.8.

Запуск (один раз):  python patch_insta_dl.py
"""
import importlib.util
import pathlib
import sys

spec = importlib.util.find_spec("insta_dl")
if spec is None or not spec.submodule_search_locations:
    sys.exit("insta_dl не установлен: python -m pip install instagram-dl")

path = pathlib.Path(list(spec.submodule_search_locations)[0]) / "backends" / "_hiker_map.py"
src = path.read_text(encoding="utf-8")

old = 'pk=str(raw["pk"]).removeprefix("highlight:"),'
new = 'pk=str(raw.get("pk") or raw.get("id") or raw.get("highlight_id") or "").removeprefix("highlight:"),'

if new in src:
    sys.exit("Патч уже применён.")
if old not in src:
    sys.exit("Нужная строка не найдена: версия insta-dl отличается. Файл: %s" % path)

path.write_text(src.replace(old, new), encoding="utf-8")
print("Готово, исправлен файл:", path)
