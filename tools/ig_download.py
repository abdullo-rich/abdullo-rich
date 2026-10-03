#!/usr/bin/env python3
"""Массовое скачивание публичных профилей Instagram (посты, рилсы, истории, актуальное).

Обёртка над insta-dl (https://github.com/subzeroid/insta-dl). Вход в Instagram не нужен,
нужен только токен HikerAPI (https://hikerapi.com, первые 100 запросов бесплатно).

Установка:
    pip install instagram-dl
    export HIKERAPI_TOKEN=ваш_токен

Примеры:
    python tools/ig_download.py nickname
    python tools/ig_download.py nick1 nick2 nick3 --dest ./out
    python tools/ig_download.py --file users.txt          # по одному нику в строке, # = комментарий

Повторный запуск докачивает только новое (--fast-update).
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def clean(name: str) -> str:
    name = name.strip().rstrip("/")
    if "instagram.com/" in name:
        name = name.split("instagram.com/", 1)[1].split("/", 1)[0].split("?", 1)[0]
    return name.lstrip("@")


def read_users(args) -> list[str]:
    users = list(args.users)
    if args.file:
        for line in Path(args.file).read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                users.append(line)
    seen, out = set(), []
    for u in map(clean, users):
        if u and u.lower() not in seen:
            seen.add(u.lower())
            out.append(u)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Массовое скачивание профилей Instagram через insta-dl")
    p.add_argument("users", nargs="*", help="ники или ссылки на профили")
    p.add_argument("--file", help="текстовый файл со списком ников")
    p.add_argument("--dest", default="instagram_downloads", help="папка для файлов")
    p.add_argument("--no-stories", action="store_true", help="не качать истории")
    p.add_argument("--no-highlights", action="store_true", help="не качать актуальное")
    p.add_argument("--concurrency", type=int, default=4, help="параллельных загрузок")
    args = p.parse_args()

    users = read_users(args)
    if not users:
        p.error("укажите хотя бы один ник или --file")
    if not shutil.which("insta-dl"):
        sys.exit("insta-dl не найден. Установите: pip install instagram-dl")
    if not os.environ.get("HIKERAPI_TOKEN"):
        sys.exit("Нет токена. Выполните: export HIKERAPI_TOKEN=ваш_токен (hikerapi.com)")

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    base = [
        "insta-dl", "--dest", str(dest),
        "--fast-update", "--latest-stamps", str(dest / "stamps.ini"),
        "--concurrency", str(args.concurrency),
    ]
    if not args.no_stories:
        base.append("--stories")
    if not args.no_highlights:
        base.append("--highlights")

    failed = []
    for i, user in enumerate(users, 1):
        print(f"\n[{i}/{len(users)}] {user}", flush=True)
        if subprocess.call(base + [user]) != 0:
            failed.append(user)

    print(f"\nГотово: {len(users) - len(failed)}/{len(users)}. Файлы в {dest.resolve()}")
    if failed:
        print("Не удалось:", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
