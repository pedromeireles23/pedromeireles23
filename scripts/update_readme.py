"""Atualiza a seção de repositórios recentes do README do perfil.

Lê os repositórios públicos do usuário pela API do GitHub, ordena pelo
último push e reescreve o trecho entre os marcadores RECENT_REPOS.
Usa apenas a biblioteca padrão do Python.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

USER = os.environ.get("GH_USER", "pedromeireles23")
TOKEN = os.environ.get("GITHUB_TOKEN")
LIMIT = int(os.environ.get("RECENT_LIMIT", "6"))
README = Path(__file__).resolve().parent.parent / "README.md"

START = "<!-- RECENT_REPOS:START -->"
END = "<!-- RECENT_REPOS:END -->"
IGNORE = {USER.lower()}
MAX_DESC = 110


def fetch_repos():
    url = (
        f"https://api.github.com/users/{USER}/repos"
        "?type=owner&sort=pushed&direction=desc&per_page=100"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-readme",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as resp:
        return json.load(resp)


def describe(repo):
    desc = " ".join((repo.get("description") or "").split())
    if len(desc) > MAX_DESC:
        desc = desc[:MAX_DESC].rsplit(" ", 1)[0].rstrip(" ,.;:—-") + "…"
    parts = [desc.replace("|", "\\|")] if desc else []
    if repo.get("homepage"):
        parts.append(f"[🔗 demo]({repo['homepage']})")
    return " · ".join(parts) or "—"


def render(repos):
    rows = [
        "| Repositório | Descrição | Linguagem | Atualizado |",
        "|---|---|:---:|:---:|",
    ]
    for repo in repos:
        pushed = datetime.strptime(repo["pushed_at"], "%Y-%m-%dT%H:%M:%SZ")
        lang = f"`{repo['language']}`" if repo.get("language") else "—"
        rows.append(
            f"| [**{repo['name']}**]({repo['html_url']}) "
            f"| {describe(repo)} | {lang} | {pushed:%d/%m/%Y} |"
        )
    return "\n".join(rows)


def main():
    repos = [
        r
        for r in fetch_repos()
        if not r["fork"] and not r["archived"] and not r["private"]
        and r["name"].lower() not in IGNORE
    ][:LIMIT]

    content = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(content):
        sys.exit(f"Marcadores {START} / {END} não encontrados em {README}")

    block = f"{START}\n{render(repos)}\n{END}"
    new = pattern.sub(lambda _: block, content)
    if new != content:
        README.write_text(new, encoding="utf-8", newline="\n")
        print(f"README atualizado com {len(repos)} repositórios.")
    else:
        print("Nada mudou.")


if __name__ == "__main__":
    main()
