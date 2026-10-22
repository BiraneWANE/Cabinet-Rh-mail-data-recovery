"""Étape 3 : classification.

Approche hybride, choisie volontairement :
- des RÈGLES explicables (config/rules.yaml) traitent l'immense majorité des cas,
  pour un coût nul et une décision que la cliente peut relire ;
- un MODÈLE DE LANGAGE (optionnel, branché via `LLMClassifier`) n'est appelé que
  sur les cas ambigus, avec le texte masqué (sans mail ni téléphone) ;
- tout ce qui reste incertain part en « à vérifier » : l'humain tranche.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import yaml

from .models import Attachment, Category
from .privacy import has_email, has_phone, mask
from .text import normalize

DEFAULT_RULES = Path(__file__).resolve().parents[2] / "config" / "rules.yaml"
YEAR_RE = re.compile(r"\b(20[01]\d|202\d)\b")
CV_SECTIONS = ["experience", "formation", "competences", "langues", "logiciels", "diplome"]


@dataclass
class Rules:
    threshold: float
    filename_weight: float
    text_weight: float
    categories: dict[str, dict[str, list[str]]]
    cv_min_sections: int

    @classmethod
    def load(cls, path: Path = DEFAULT_RULES) -> Rules:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls(
            threshold=raw["threshold"],
            filename_weight=raw["filename_weight"],
            text_weight=raw["text_weight"],
            categories=raw["categories"],
            cv_min_sections=raw.get("cv_min_sections", 2),
        )


class LLMClassifier(Protocol):
    """Interface d'un classifieur à base de modèle de langage (cas ambigus)."""

    def classify(self, filename: str, masked_text: str, labels: list[str]) -> tuple[str, float]:
        ...


def score(att: Attachment, rules: Rules) -> dict[str, float]:
    fname = normalize(Path(att.path).stem.split("_", 1)[-1])
    body = normalize(att.text)
    scores: dict[str, float] = {}
    for cat, kw in rules.categories.items():
        s = sum(rules.filename_weight for k in kw.get("filename", []) if k in fname)
        s += sum(rules.text_weight for k in kw.get("text", []) if k in body)
        if s:
            scores[cat] = s
    return scores


def classify(att: Attachment, rules: Rules, llm: LLMClassifier | None = None) -> Attachment:
    att.has_email = has_email(att.text)
    att.has_phone = has_phone(att.text)
    scores = score(att, rules)

    if scores:
        best, best_score = max(scores.items(), key=lambda kv: kv[1])
        total = sum(scores.values())
        att.category = Category(best)
        att.confidence = round(best_score / total, 2)
        att.reason = f"règles : {best}={best_score}"
    else:
        best_score = 0.0

    if best_score < rules.threshold:
        if llm is not None and att.text:
            label, conf = llm.classify(
                Path(att.path).name, mask(att.text[:4000]), [c.value for c in Category]
            )
            att.category, att.confidence, att.reason = Category(label), conf, "modèle de langage"
        else:
            att.category, att.reason = Category.A_VERIFIER, "score sous le seuil"

    # Règle métier : un CV doit ressembler à un CV ET permettre de recontacter
    if att.category is Category.CV:
        body = normalize(att.text)
        n_sections = sum(1 for s in CV_SECTIONS if s in body)
        if att.text and n_sections < rules.cv_min_sections:
            att.category, att.reason = Category.A_VERIFIER, "nom de CV mais contenu atypique"
        elif att.text and not (att.has_email or att.has_phone):
            att.category, att.reason = Category.CV_ANONYME, "CV sans mail ni téléphone"

    year = YEAR_RE.findall(Path(att.path).name) or YEAR_RE.findall(att.text[:3000])
    att.year = year[0] if year else att.mail_date[:4]
    return att
