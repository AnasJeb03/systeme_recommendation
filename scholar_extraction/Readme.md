# 📚 Module d’Extraction de Publications Scientifiques

## Vue d’ensemble

Ce module fait partie d’un système de collecte automatisée des publications académiques depuis différentes plateformes en ligne. Il repose sur un pipeline complet d'extraction, de nettoyage, de stockage et d'analyse des données, à destination des laboratoires et chercheurs.

## Architecture Fonctionnelle

### 1. Sources d’Extraction

* **GoogleScholarExtractor** : Récupération des publications à partir des profils d’auteurs Google Scholar via `scholarly`.
* **HALExtractor** : Interrogation de l’API HAL pour récupérer des publications francophones issues de l’archive ouverte.
* **SemanticScholarExtractor** : Accès aux données enrichies de Semantic Scholar (résumés, DOI, citations...).

### 2. Traitement

* **DataCleaner** : Nettoyage des titres/abstracts, résumé automatique, extraction de mots-clés.
* **StatsGenerator** : Calcul des métriques : nombre de publications, citations totales, moyenne, etc.

### 3. Persistance

* **MongoConnector** et **ScholarRepository** : Connexion à MongoDB et gestion des collections `auteurs`, `Publications`, `Statistiques`.

---

## Fonctionnalités Clés

### 🔍 Extraction par Chercheur

```python
process_researcher("Jean Dupont", affiliation="Université de Paris", sources=["google_scholar", "hal"])
```

* Recherche d’un chercheur sur plusieurs sources.
* Déduplication des publications.
* Stockage structuré des métadonnées.
* Enrichissement avec mots-clés et statistiques.

### 🔑 Extraction par Mot-clé

```python
keywords = ["data mining", "apprentissage automatique"]
process_publications_by_keywords(keywords, languages=["fr", "en"])
```

* Recherche ciblée sur les bases de données scientifiques.
* Détection automatique de la langue (Google Scholar).
* Insertion en lot dans MongoDB avec enrichissement des métadonnées.

### ⚙️ Traitement Massif

```python
chercheurs = ["Marie Curie", "Pierre Curie"]
process_multiple_researchers(chercheurs)
```

* Exécution séquentielle ou parallèle avec temporisation.
* Idéal pour traiter une liste de chercheurs ou mots-clés à grande échelle.

---

## Stockage des Données

### Chercheurs (`auteurs`)

```json
{
  "nom": "Marie Curie",
  "affiliation": "Sorbonne",
  "h_index": 32,
  "citations_total": 5000,
  "interests": ["radioactivité", "chimie"],
  "sources": ["google_scholar", "hal"],
  "date_creation": "2025-05-28T10:20:00"
}
```

### Publications (`Publications`)

```json
{
  "title": "Étude sur les éléments radioactifs",
  "abstract_full": "...",
  "abstract_short": "...",
  "authors": ["Marie Curie"],
  "year": "1903",
  "keywords": ["radioactivité", "chimie"],
  "source": "hal",
  "citations": 120,
  "url": "https://hal.archives-ouvertes.fr/...",
  "date_extraction": "2025-05-28T10:22:00"
}
```

---

## Pré-requis Techniques

* Python 3.10+
* Bibliothèques : `scholarly`, `requests`, `pymongo`, `langdetect`, `nltk`, `pandas`
* MongoDB actif (local ou distant)
* Clé API facultative pour Semantic Scholar

---

## Robustesse et Performance

* 🔄 Détection des doublons par titre + année
* 🧠 Extraction de mots-clés techniques par domaine
* ⏱️ Gestion de la pagination et des délais API
* 💥 Gestion des erreurs, timeouts et reconnexions MongoDB

---

## Améliorations Futures

* Interface graphique pour visualisation des données
* Mécanisme de mise à jour incrémentale
* API REST ou microservice Flask
* Export CSV/PDF des statistiques

---

## Contexte

Ce module a été développé dans le cadre d’un stage universitaire. Il vise à automatiser l’analyse bibliographique pour un laboratoire de recherche, en regroupant les données issues de différentes sources dans une base unifiée et enrichie.
