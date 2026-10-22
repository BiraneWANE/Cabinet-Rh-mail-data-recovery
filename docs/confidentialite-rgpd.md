# Confidentialité et RGPD

Les archives traitées contiennent des données personnelles de milliers de candidats et de contacts clients. Le projet a été conçu pour que **ces données ne quittent jamais le poste de la cliente**, et pour que ce dépôt public n'en contienne aucune trace.

## Ce qui est publié

- le code du pipeline ;
- les règles de classification (mots‑clés métier, sans aucun nom) ;
- des chiffres **agrégés** (nombre de CV, de contrats, de doublons...) ;
- un générateur de données **entièrement fictives** (noms inventés, sociétés « Alpha », « Beta »..., adresses en `example.com`).

## Ce qui n'est jamais publié

CV, noms de candidats ou de clients, adresses mail, numéros de téléphone, contrats, factures, recensements, portefeuille clients, sauvegardes .pst, noms des titulaires des boîtes.

## Garde‑fous techniques

| Niveau | Mécanisme |
|---|---|
| 1. Fichiers | `.gitignore` exclut tous les formats de données |
| 2. Avant commit | hook `.githooks/pre-commit` qui lance `scripts/check_no_pii.py` |
| 3. Après push | GitHub Actions relance le même contrôle ; l'intégration échoue si une donnée apparaît |
| 4. Dans le pipeline | seul le domaine de l'expéditeur est conservé ; les boîtes sont pseudonymisées |
| 5. IA | texte masqué (`[EMAIL]`, `[TEL]`) avant tout appel à un modèle de langage |

## Principes RGPD appliqués

| Principe | Application |
|---|---|
| Minimisation | les CV anonymes, quittances, RIB, diplômes et documents privés sortent de la base |
| Finalité | la base sert uniquement à recontacter des candidats et clients du cabinet |
| Exactitude | en cas de versions multiples d'un CV, la plus récente est conservée |
| Sécurité | traitement local, sources conservées en lecture seule |
| Limitation de conservation | les documents retirés sont isolés pour que la cliente décide de leur suppression |

Point d'attention transmis à la cliente : avant de recontacter d'anciens candidats, prévoir un message d'information sur la conservation de leur CV et la possibilité de demander sa suppression.
