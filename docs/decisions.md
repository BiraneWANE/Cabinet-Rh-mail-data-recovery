# Choix techniques et arbitrages

## 1. Export .pst plutôt que glisser‑déposer
Le glisser‑déposer depuis Outlook ne copie pas tout (éléments envoyés, sous‑dossiers, éléments supprimés). L'export .pst complet est la seule sauvegarde fiable. Il est fait **avant** toute action et n'est plus jamais modifié.

## 2. Règles métier d'abord, IA ensuite
| Option | Coût | Explicable | Rejouable | Retenue |
|---|---|---|---|---|
| Tout par modèle de langage | élevé sur 8 600 fichiers | faible | variable | non |
| Tout par règles | nul | total | total | insuffisant seul |
| **Règles + IA sur les cas ambigus + humain** | faible | fort | oui | ✅ |

Les règles ont été écrites avec la cliente, à partir de son vocabulaire de recruteuse en expertise comptable.

## 3. Deux niveaux de dédoublonnage
Un même CV circule sous plusieurs formes : envoyé en Word puis en PDF, transféré d'une boîte à l'autre, renvoyé à plusieurs clients. L'empreinte binaire seule rate les doublons de format ; l'empreinte de texte normalisé les attrape. Résultat sur les vraies archives : 3 613 CV avant fusion, 3 028 après.

## 4. Ne jamais fusionner automatiquement deux versions différentes d'un CV
Un candidat qui a mis à jour son CV entre 2016 et 2021 a deux documents réellement différents. Le pipeline les signale (`versions_to_compare`) et l'humain tranche en comparant le contenu.

## 5. « Un CV sans contact n'est pas un CV »
Règle de la cliente : un CV anonymisé (préparé pour être envoyé à un client) ne permet pas de recontacter le candidat. 1 846 documents ont été retirés pour cette raison.

## 6. Rien n'est supprimé par le programme
Chaque document écarté est rangé dans un dossier qui dit pourquoi : `_DOUBLONS`, `_RETIRES/CV_anonymes`, `_RETIRES/Sans_interet`, `_RETIRES/Hors_perimetre`, `_A_VERIFIER`. La suppression reste une décision humaine.

## 7. Tout en PDF
Exigence de la cliente : une base homogène, lisible partout, non modifiable par erreur. Environ 2 900 fichiers Word ont été convertis.

## 8. Les noms de fichiers sont la première base de données
En attendant le CRM, le nom de fichier porte l'information utile : `NOM Prénom` pour chercher un candidat, `Contrat_Société_Année` pour retrouver un historique client. Ces conventions sont pensées pour être importées telles quelles dans le futur CRM.
