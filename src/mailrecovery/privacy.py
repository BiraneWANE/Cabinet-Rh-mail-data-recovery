"""Détection des coordonnées personnelles.

Sert à deux choses :
1. une règle métier de la cliente : un CV sans mail ni téléphone ne permet pas
   de recontacter le candidat, il sort de la base ;
2. la protection des données : on sait ce qui contient des données personnelles,
   et rien de tout ça ne quitte le poste de la cliente.
"""

from __future__ import annotations

import re

EMAIL_RE = re.compile(r"[\w.+\-]+@[\w\-]+\.[\w.\-]+")
# Numéros français : formats avec espaces, points, tirets, indicatif +33 ou collés
PHONE_RE = re.compile(r"(?:(?:\+|00)33\s?[1-9]|0[1-9])(?:[\s.\-]?\d{2}){4}")


def has_email(text: str) -> bool:
    return bool(EMAIL_RE.search(text))


def has_phone(text: str) -> bool:
    return bool(PHONE_RE.search(text))


def mask(text: str) -> str:
    """Remplace mails et téléphones : utilisé pour tout log ou export de contrôle."""
    text = EMAIL_RE.sub("[EMAIL]", text)
    return PHONE_RE.sub("[TEL]", text)
