#!/usr/bin/env python3
"""Garde-fou : refuse tout envoi qui contiendrait des données personnelles.

Lancé avant chaque commit (hook git) et à chaque push (GitHub Actions).
Bloque :
- les fichiers de données (.pst, .eml, .pdf, .docx, .xlsx...) ;
- toute adresse mail hors domaines fictifs réservés (example.com, example.org) ;
- tout numéro de téléphone français écrit en clair.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_EXT = {".pst", ".ost", ".eml", ".msg", ".mbox", ".pdf", ".doc", ".docx",
                 ".odt", ".rtf", ".xls", ".xlsx", ".ods", ".csv", ".zip"}
ALLOWED_DOMAINS = ("example.com", "example.org", "users.noreply.github.com", "anthropic.com")
EMAIL_RE = re.compile(r"[\w.+\-]+@([\w\-]+\.[\w.\-]+)")
PHONE_RE = re.compile(r"(?:(?:\+|00)33\s?[1-9]|\b0[1-9])(?:[\s.\-]?\d{2}){4}\b")
SKIP = {"scripts/check_no_pii.py"}
# Documents produits par le projet lui-même, sans aucune donnée personnelle
ALLOWED_FILES = {"docs/schema-architecture.pdf"}


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         capture_output=True, text=True, check=True).stdout
    return [Path(p) for p in out.splitlines() if p]


def main() -> int:
    problems = []
    for f in tracked_files():
        if f.as_posix() in SKIP or not f.exists():
            continue
        if f.suffix.lower() in FORBIDDEN_EXT and f.as_posix() not in ALLOWED_FILES:
            problems.append(f"{f} : type de fichier interdit (données)")
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for m in EMAIL_RE.finditer(line):
                dom = m.group(1).lower()
                if not dom.endswith(ALLOWED_DOMAINS) and "{" not in m.group(0):
                    problems.append(f"{f}:{n} : adresse mail réelle possible")
            if PHONE_RE.search(line):
                problems.append(f"{f}:{n} : numéro de téléphone possible")
    if problems:
        print("ENVOI BLOQUÉ, données personnelles possibles :")
        print("\n".join(f"  - {p}" for p in problems))
        return 1
    print("OK : aucune donnée personnelle détectée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
