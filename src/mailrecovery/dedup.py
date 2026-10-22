"""Étape 4 : dédoublonnage, à deux niveaux.

1. Doublon exact : même empreinte binaire (sha256), le fichier est identique
   octet par octet (même pièce jointe renvoyée dans plusieurs mails ou boîtes).
2. Doublon de contenu : même empreinte de texte, le fichier diffère (Word et PDF,
   nouvelle mise en page) mais dit la même chose.

Pour chaque groupe, on garde UNE version : la plus récente, et à date égale la
plus complète (texte le plus long). Les autres restent tracées, jamais effacées.
Les CV d'une même personne aux contenus différents (mise à jour du parcours) ne
sont pas fusionnés automatiquement : ils sont signalés pour comparaison.
"""

from __future__ import annotations

from collections import defaultdict

from .models import Attachment, Category


def _best(group: list[Attachment]) -> Attachment:
    return max(group, key=lambda a: (a.mail_date, len(a.text), a.path.suffix.lower() == ".pdf"))


def deduplicate(items: list[Attachment]) -> tuple[list[Attachment], list[Attachment]]:
    """Renvoie (uniques, doublons)."""
    keep: list[Attachment] = []
    dups: list[Attachment] = []

    by_hash: dict[str, list[Attachment]] = defaultdict(list)
    for a in items:
        by_hash[a.sha256].append(a)

    survivors = []
    for group in by_hash.values():
        best = _best(group)
        survivors.append(best)
        for other in group:
            if other is not best:
                other.duplicate_of = best.sha256[:10]
                dups.append(other)

    by_fp: dict[str, list[Attachment]] = defaultdict(list)
    for a in survivors:
        (by_fp[a.text_fingerprint] if a.text_fingerprint else keep).append(a)
    for group in by_fp.values():
        best = _best(group)
        keep.append(best)
        for other in group:
            if other is not best:
                other.duplicate_of = best.sha256[:10]
                dups.append(other)
    return keep, dups


def versions_to_compare(items: list[Attachment]) -> dict[str, list[Attachment]]:
    """CV d'une même personne avec des contenus différents : à départager à la main."""
    groups: dict[str, list[Attachment]] = defaultdict(list)
    for a in items:
        if a.category is Category.CV and a.entity:
            groups[a.entity].append(a)
    return {k: v for k, v in groups.items() if len(v) > 1}
