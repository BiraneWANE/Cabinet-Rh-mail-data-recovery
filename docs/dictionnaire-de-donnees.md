# Dictionnaire de données

Ce document décrit la **structure** des bases livrées à la cliente, sans aucun contenu réel.

## 1. Base candidats

Un fichier PDF par candidat, nommé `NOM Prénom.pdf`, dans `1_BASE_CANDIDATS/CV_complets/`.

Critères d'entrée dans la base :

| Critère | Règle |
|---|---|
| Ressemble à un CV | au moins 2 rubriques typiques (expérience, formation, compétences, langues, logiciels, diplôme) |
| Candidat joignable | au moins un mail ou un téléphone dans le document |
| Unique | ni doublon exact, ni doublon de contenu d'un CV déjà retenu |
| Format | PDF uniquement |

## 2. Base administrative

| Dossier | Contenu | Convention de nom |
|---|---|---|
| `Contrats_et_conventions` | contrats clients, conventions, conditions générales signées | `Contrat_<Société>_<Année>.pdf` |
| `Factures_et_avoirs` | factures émises, avoirs | `Facture_<Client>_<Année>.pdf` |
| `Embauches_et_promesses` | promesses et confirmations d'embauche | `Embauche_<Société>_<Année>.pdf` |
| `Offres_et_fiches_de_poste` | offres publiées, fiches de poste clients | `Offre_<Intitulé>_<Année>.pdf` |
| `Documents_internes` | documents propres au cabinet | `Interne_<Objet>_<Année>.pdf` |

## 3. Portefeuille clients (classeur Excel)

| Onglet | Une ligne = | Colonnes principales |
|---|---|---|
| Lisez‑moi | mode d'emploi du classeur | |
| Placements | un candidat placé | candidat, poste, société cliente, date, source |
| Clients | une société cliente | société, ville, nombre de placements, dernière activité |
| Contacts clients | un interlocuteur chez un client | société, fonction, domaine mail |
| Clients à relancer | un client prioritaire | société, motif de priorité, dernière activité |
| Candidats présentés | une présentation sans placement | candidat, société, date |
| Prospects | une société jamais cliente | société, origine |
| À vérifier | une ligne incertaine | motif du doute |

## 4. Recensement de contrôle (`RECENSEMENT.xlsx`)

Généré par le pipeline, un onglet par statut : `Résumé`, `Base`, `À vérifier`, `Retirés`, `Doublons`.

| Colonne | Type | Description |
|---|---|---|
| `final_name` | texte | nom du fichier dans la base |
| `category` | catégorie | une des 12 catégories (voir ci‑dessous) |
| `entity` | texte | « NOM Prénom » ou société |
| `year` | AAAA | année du document (nom de fichier, contenu, ou date du mail) |
| `confidence` | 0 à 1 | part du score de la catégorie gagnante |
| `reason` | texte | règle ou modèle qui a décidé |
| `mailbox` | texte | boîte source pseudonymisée (`boite_A`...) |
| `mail_date` | date ISO | date du mail d'origine |
| `direction` | reçu / envoyé | sens du mail |
| `sender_domain` | texte | domaine de l'expéditeur (jamais l'adresse complète) |
| `has_email`, `has_phone` | booléen | présence de coordonnées dans le document |
| `duplicate_of` | texte | identifiant du document conservé, si doublon |
| `sha256` | texte | empreinte binaire du fichier |

## 5. Catégories

| Catégorie | Destination | Exemple |
|---|---|---|
| `cv` | base candidats | CV complet avec contact |
| `contrat`, `facture`, `embauche`, `offre`, `interne`, `test` | base administrative | |
| `suivi` | portefeuille clients | tableau de suivi de placements |
| `cv_anonyme` | retiré | CV transmis à un client, coordonnées effacées |
| `sans_interet` | retiré | quittance de loyer, ancien RIB, diplôme, attestation |
| `prive` | retiré | document personnel hors activité |
| `a_verifier` | validation humaine | score trop faible pour décider |
