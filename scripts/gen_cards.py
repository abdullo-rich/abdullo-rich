"""Генератор SVG-карточек для профиля.

Тянет свежие данные через gh CLI (видит и приватные репозитории)
и рисует две карточки на русском в зелёной терминальной гамме.

Запуск:  python scripts/gen_cards.py
"""

import json
import math
import subprocess
from pathlib import Path

USER = "abdullo-rich"
GH = r"C:\Users\SmartSystem\gh-cli\bin\gh.exe"
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"

# Репозитории, которые не отражают собственный код (скопированные upstream-проекты).
EXCLUDED_REPOS = {"my-astrbot"}

BG = "#0d1117"
GREEN = "#39ff14"
TEXT = "#c9d1d9"
DIM = "#8b949e"
BORDER = "#1f6f2f"

# Цвета языков (как в GitHub Linguist)
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "PowerShell": "#5391FE",  # светлее оригинального #012456 — тот не виден на тёмном фоне
    "Batchfile": "#C1F12E",
    "Shell": "#89e051",
    "Vue": "#41b883",
    "Kotlin": "#A97BFF",
    "Java": "#b07219",
    "Dockerfile": "#384d54",
}
FALLBACK_COLORS = ["#39ff14", "#2dde98", "#00b8d4", "#ffb86c", "#ff79c6"]


def gh_json(*args):
    """Вызвать gh и разобрать JSON-ответ."""
    result = subprocess.run(
        [GH, *args], capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} -> {result.stderr.strip()}")
    return json.loads(result.stdout)


def esc(text):
    """Экранировать спецсимволы XML."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def collect_languages():
    """Собрать байты по языкам из всех значимых репозиториев."""
    repos = gh_json("repo", "list", USER, "--limit", "100", "--json", "name")
    totals = {}
    for repo in repos:
        name = repo["name"]
        if name in EXCLUDED_REPOS or name == USER:
            continue
        try:
            langs = gh_json("api", f"repos/{USER}/{name}/languages")
        except RuntimeError:
            continue
        for lang, size in langs.items():
            totals[lang] = totals.get(lang, 0) + size
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


def collect_stats():
    """Собрать сводные показатели профиля."""
    query = """
    {
      user(login: "%s") {
        followers { totalCount }
        repositories(ownerAffiliations: OWNER) { totalCount }
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
          totalPullRequestContributions
          totalIssueContributions
        }
      }
    }
    """ % USER
    data = gh_json("api", "graphql", "-f", f"query={query}")["data"]["user"]
    contrib = data["contributionsCollection"]
    commits = (
        contrib["totalCommitContributions"]
        + contrib["restrictedContributionsCount"]
    )
    return {
        "Репозиториев": data["repositories"]["totalCount"],
        "Коммитов за год": commits,
        "Pull request'ов": contrib["totalPullRequestContributions"],
        "Issues": contrib["totalIssueContributions"],
        "Подписчиков": data["followers"]["totalCount"],
    }


# Стили заданы атрибутами, а не CSS-блоком: GitHub прогоняет картинки через
# свой прокси и может вырезать <style>, тогда карточка станет нечитаемой.
FONT = "'Segoe UI', Ubuntu, Helvetica, sans-serif"


def text_el(x, y, content, size, color, weight=400, anchor="start"):
    """Текстовый элемент с явными атрибутами оформления."""
    return (
        f'  <text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{esc(content)}</text>\n'
    )


def frame(width, height, title):
    """Общая рамка карточки с заголовком."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">\n'
        f'  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" '
        f'fill="{BG}" stroke="{BORDER}" stroke-width="1"/>\n'
        + text_el(22, 34, title, 17, GREEN, 600)
    )


def render_languages(langs):
    """Карточка «Языки» — кольцевая диаграмма и легенда."""
    width, height = 400, 230
    total = sum(langs.values()) or 1
    top = list(langs.items())[:5]

    parts = [frame(width, height, "Языки")]

    # Кольцевая диаграмма
    cx, cy, r, stroke = 300, 130, 52, 26
    circumference = 2 * math.pi * r
    offset = 0.0
    for index, (lang, size) in enumerate(top):
        share = size / total
        color = LANG_COLORS.get(lang, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])
        dash = share * circumference
        parts.append(
            f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="{stroke}" stroke-dasharray="{dash:.2f} {circumference - dash:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})"/>\n'
        )
        offset += dash

    # Легенда
    y = 78
    for index, (lang, size) in enumerate(top):
        share = size / total * 100
        color = LANG_COLORS.get(lang, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])
        parts.append(f'  <rect x="22" y="{y - 10}" width="11" height="11" rx="2" fill="{color}"/>\n')
        parts.append(text_el(42, y, lang, 13, TEXT))
        parts.append(text_el(185, y, f"{share:.1f}%", 13, GREEN, 600, "end"))
        y += 26

    parts.append(text_el(22, height - 16, "по всем репозиториям, включая приватные", 11, DIM))
    parts.append("</svg>\n")
    return "".join(parts)


def render_stats(stats):
    """Карточка «Статистика» — список показателей."""
    width, height = 400, 230
    parts = [frame(width, height, "Статистика")]

    y = 78
    for label, value in stats.items():
        parts.append(text_el(22, y, label, 13, TEXT))
        parts.append(text_el(width - 22, y, value, 13, GREEN, 600, "end"))
        parts.append(
            f'  <line x1="22" y1="{y + 9}" x2="{width - 22}" y2="{y + 9}" '
            f'stroke="{BORDER}" stroke-width="1" opacity="0.4"/>\n'
        )
        y += 28

    parts.append(text_el(22, height - 16, "включая приватные репозитории", 11, DIM))
    parts.append("</svg>\n")
    return "".join(parts)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    langs = collect_languages()
    stats = collect_stats()

    (OUT_DIR / "languages.svg").write_text(render_languages(langs), encoding="utf-8")
    (OUT_DIR / "stats.svg").write_text(render_stats(stats), encoding="utf-8")

    print("Языки:", ", ".join(f"{k} {v}" for k, v in list(langs.items())[:5]))
    print("Показатели:", stats)
    print("Готово ->", OUT_DIR)


if __name__ == "__main__":
    main()
