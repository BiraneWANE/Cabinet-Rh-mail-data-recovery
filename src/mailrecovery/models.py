"""Structures de données partagées par toutes les étapes du pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path


class Category(str, Enum):
    """Catégories cibles de la base finale."""

    CV = "cv"                          # CV complet, exploitable pour la base candidats
    CV_ANONYME = "cv_anonyme"          # CV sans aucun moyen de contact : retiré
    CONTRAT = "contrat"                # contrats, conventions, CGV signées
    EMBAUCHE = "embauche"              # promesses d'embauche, confirmations
    FACTURE = "facture"                # factures et avoirs
    OFFRE = "offre"                    # offres d'emploi, fiches de poste
    SUIVI = "suivi"                    # tableaux de suivi de placements
    INTERNE = "interne"                # documents internes de l'entreprise
    TEST = "test"                      # tests techniques passés par les candidats
    SANS_INTERET = "sans_interet"      # diplômes, attestations, quittances, anciens RIB...
    PRIVE = "prive"                    # hors périmètre professionnel
    A_VERIFIER = "a_verifier"          # doute : validation humaine obligatoire


# Catégories qui alimentent la base finale
KEEP = {
    Category.CV,
    Category.CONTRAT,
    Category.EMBAUCHE,
    Category.FACTURE,
    Category.OFFRE,
    Category.SUIVI,
    Category.INTERNE,
    Category.TEST,
}


@dataclass
class Attachment:
    """Une pièce jointe extraite d'un mail, et tout ce que le pipeline apprend sur elle."""

    path: Path
    mailbox: str                 # identifiant de la boîte source (pseudonymisé : boite_A...)
    mail_date: str = ""          # date ISO du mail d'origine
    mail_subject: str = ""
    sender_domain: str = ""      # on garde le domaine, jamais l'adresse complète
    direction: str = "recu"      # "recu" ou "envoye"
    sha256: str = ""
    text: str = field(default="", repr=False)
    text_fingerprint: str = ""
    has_email: bool = False
    has_phone: bool = False
    category: Category = Category.A_VERIFIER
    confidence: float = 0.0
    reason: str = ""             # règle ou modèle qui a décidé (traçabilité)
    entity: str = ""             # NOM Prénom, ou société pour les contrats/factures
    year: str = ""
    duplicate_of: str = ""
    final_name: str = ""

    def to_row(self) -> dict:
        row = asdict(self)
        row["path"] = str(self.path)
        row["category"] = self.category.value
        row.pop("text")
        return row
