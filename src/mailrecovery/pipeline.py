"""Orchestration complète : de plusieurs boîtes mail à une base fusionnée.

    sources (.pst ou dossiers .eml)
      -> extraction des pièces jointes   (extract)
      -> lecture du texte                (text)
      -> classification                  (classify + privacy)
      -> fusion des boîtes + doublons    (dedup)
      -> renommage normalisé             (naming)
      -> conversion PDF et rangement     (convert)
      -> recensement Excel               (report)

Le pipeline ne supprime jamais rien : chaque document écarté est rangé dans un
dossier qui dit pourquoi (_DOUBLONS, _RETIRES, _A_VERIFIER).
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .classify import LLMClassifier, Rules, classify
from .convert import to_pdf
from .dedup import deduplicate
from .extract import extract_attachments, pst_to_eml
from .models import Attachment, Category
from .naming import final_name, unique
from .report import write_report
from .text import fingerprint, read_text

log = logging.getLogger(__name__)

LAYOUT: dict[Category, str] = {
    Category.CV: "1_BASE_CANDIDATS/CV_complets",
    Category.CONTRAT: "2_BASE_ADMINISTRATIVE/Contrats_et_conventions",
    Category.EMBAUCHE: "2_BASE_ADMINISTRATIVE/Embauches_et_promesses",
    Category.FACTURE: "2_BASE_ADMINISTRATIVE/Factures_et_avoirs",
    Category.OFFRE: "2_BASE_ADMINISTRATIVE/Offres_et_fiches_de_poste",
    Category.INTERNE: "2_BASE_ADMINISTRATIVE/Documents_internes",
    Category.TEST: "2_BASE_ADMINISTRATIVE/Tests_candidats",
    Category.SUIVI: "3_PORTEFEUILLE_CLIENTS/Tableaux_de_suivi",
    Category.A_VERIFIER: "_A_VERIFIER",
    Category.CV_ANONYME: "_RETIRES/CV_anonymes",
    Category.SANS_INTERET: "_RETIRES/Sans_interet",
    Category.PRIVE: "_RETIRES/Hors_perimetre",
}


@dataclass
class Source:
    mailbox: str   # identifiant pseudonymisé, ex. "boite_A"
    path: Path     # un fichier .pst ou un dossier de .eml


def run(
    sources: list[Source],
    output: Path,
    rules: Rules | None = None,
    own_domains: set[str] | None = None,
    llm: LLMClassifier | None = None,
    convert: bool = True,
) -> dict:
    rules = rules or Rules.load()
    output.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="mailrecovery_"))
    items: list[Attachment] = []
    n_mails = 0

    # 1 à 3 : une boîte après l'autre
    for src in sources:
        eml_root = pst_to_eml(src.path, work / src.mailbox / "eml") if src.path.suffix.lower() == ".pst" else src.path
        found, n = extract_attachments(eml_root, work / src.mailbox / "pj", src.mailbox, own_domains)
        n_mails += n
        for att in found:
            att.text = read_text(att.path)
            att.text_fingerprint = fingerprint(att.text)
            classify(att, rules, llm)
        items.extend(found)

    # 4 : fusion de toutes les boîtes, puis doublons inter-boîtes
    kept, dups = deduplicate(items)

    # 5 et 6 : nom final, conversion PDF, rangement
    taken: set[str] = set()
    for att in kept:
        folder = output / LAYOUT[att.category]
        folder.mkdir(parents=True, exist_ok=True)
        base = final_name(att)
        pdf = to_pdf(att.path, work / "pdf") if convert else None
        if pdf is not None:
            name = unique(base, taken)
            shutil.copy2(pdf, folder / name)
        else:  # format non convertible (tableur, image) : copié avec son extension
            name = unique(Path(base).with_suffix(att.path.suffix).name, taken)
            shutil.copy2(att.path, folder / name)
        att.final_name = name
    dup_dir = output / "_DOUBLONS"
    dup_dir.mkdir(exist_ok=True)
    for i, att in enumerate(dups, 1):
        att.final_name = f"{i:04d}_{att.path.name}"
        shutil.copy2(att.path, dup_dir / att.final_name)

    # 7 : recensement
    stats = write_report(output / "RECENSEMENT.xlsx", kept, dups, n_mails)
    shutil.rmtree(work, ignore_errors=True)
    log.info("terminé : %s", stats)
    return stats
