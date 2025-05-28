# Module d'Extraction de Données Scientifiques

## Vue d'ensemble

Ce module fait partie d'un système complet d'extraction et d'analyse de données bibliographiques scientifiques. Il permet d'extraire automatiquement des publications académiques depuis plusieurs sources majeures et de les traiter pour générer des statistiques et analyses.

## Architecture du Système

Le système est structuré autour de plusieurs composants principaux :

### 1. Extracteurs de Données
- **GoogleScholarExtractor** : Interface avec Google Scholar pour récupérer des profils d'auteurs et leurs publications
- **HALExtractor** : Interface avec l'API HAL (Hyper Articles en Ligne) pour extraire des publications françaises
- **SemanticScholarExtractor** : Interface avec Semantic Scholar pour des données bibliographiques enrichies

### 2. Processeurs de Données
- **DataCleaner** : Nettoyage et normalisation des données extraites
- **StatsGenerator** : Génération de statistiques et métriques bibliographiques

### 3. Couche de Persistance
- **ScholarRepository** : Interface avec MongoDB pour le stockage des données

## Fonctionnalités Principales

### Extraction par Chercheur

Le système permet d'extraire toutes les publications d'un chercheur spécifique à partir de son nom et optionnellement de son affiliation :

```python
process_researcher("Nom du Chercheur", affiliation="Université", sources=["google_scholar", "hal", "semantic_scholar"])
```

**Caractéristiques :**
- Recherche multi-sources avec déduplication automatique
- Extraction des métriques (h-index, nombre de citations, etc.)
- Stockage unifié des données hétérogènes
- Génération automatique de statistiques

### Extraction par Mots-clés

Extraction massive de publications selon des thématiques spécifiques :

```python
process_publications_by_keywords(["machine learning", "intelligence artificielle"], languages=["fr", "en"])
```

**Caractéristiques :**
- Recherche thématique sur plusieurs bases de données
- Filtrage par langue
- Traitement par lots pour optimiser les performances
- Gestion robuste des timeouts et erreurs

### Traitement en Masse

Possibilité de traiter plusieurs chercheurs simultanément avec gestion des délais pour respecter les limites des APIs.

## Sources de Données

### Google Scholar
- **Avantages** : Couverture large, métriques de citations, profils complets
- **Limitations** : Limites de taux, données parfois incomplètes
- **Données extraites** : Profils d'auteurs, publications, citations, h-index, i10-index

### HAL (Hyper Articles en Ligne)
- **Avantages** : Archive ouverte française, données structurées, API stable
- **Limitations** : Principalement francophone, pas de métriques de citations
- **Données extraites** : Publications, abstracts, métadonnées bibliographiques

### Semantic Scholar
- **Avantages** : Données enrichies, abstracts complets, API fiable
- **Limitations** : Couverture variable selon les domaines
- **Données extraites** : Publications avec abstracts, citations, DOI

## Traitement des Données

### Nettoyage et Normalisation
- Déduplication intelligente basée sur titre et année
- Nettoyage des titres et abstracts
- Extraction automatique de mots-clés techniques
- Génération de résumés courts

### Enrichissement
- Extraction de mots-clés spécialisés par domaine
- Analyse linguistique pour la détection de langue
- Classification thématique automatique

### Gestion des Conflits
- Fusion intelligente des données provenant de sources multiples
- Mise à jour incrémentale des informations
- Préservation de la traçabilité des sources

## Optimisations Techniques

### Gestion de la Performance
- **Traitement par lots** : Les grandes extractions sont divisées en lots pour éviter les timeouts
- **Pagination intelligente** : Gestion automatique de la pagination des APIs
- **Délais adaptatifs** : Respect des limites de taux de chaque API

### Robustesse
- **Gestion d'erreurs** : Capture et gestion des exceptions avec continuation du traitement
- **Timeouts configurables** : Protection contre les blocages
- **Retry logic** : Nouvelles tentatives automatiques en cas d'échec temporaire

### Scalabilité
- **Architecture modulaire** : Séparation claire entre extraction, traitement et stockage
- **Extensibilité** : Facilité d'ajout de nouvelles sources de données
- **Configuration flexible** : Paramétrage fin des comportements d'extraction

## Structure des Données

### Chercheurs
```json
{
  "nom": "Nom du chercheur",
  "affiliation": "Institution",
  "h_index": 25,
  "i10_index": 40,
  "citations_total": 1500,
  "interests": ["machine learning", "data mining"],
  "sources": ["google_scholar", "hal"],
  "date_creation": "2024-01-15T10:30:00"
}
```

### Publications
```json
{
  "title": "Titre de la publication",
  "abstract_full": "Résumé complet",
  "abstract_short": "Résumé court généré",
  "authors": ["Auteur 1", "Auteur 2"],
  "year": "2023",
  "venue": "Nom de la revue/conférence",
  "citations": 15,
  "keywords": ["mot-clé 1", "mot-clé 2"],
  "source": "google_scholar",
  "date_extraction": "2024-01-15T10:30:00"
}
```

## Utilisation

### Configuration Préalable
1. Installation des dépendances Python (scholarly, requests, pandas, etc.)
2. Configuration de la base de données MongoDB
3. Paramétrage des délais et limites dans le fichier de configuration

### Exemples d'Utilisation

**Extraction d'un chercheur unique :**
```python
process_researcher("Marie Curie", sources=["google_scholar", "hal"])
```

**Extraction thématique :**
```python
keywords = ["deep learning", "neural networks", "artificial intelligence"]
process_publications_by_keywords(keywords, languages=["en"])
```

**Traitement en masse :**
```python
chercheurs = ["Albert Einstein", "Marie Curie", "Alan Turing"]
process_multiple_researchers(chercheurs)
```

## Considérations Techniques

### Respect des APIs
- Délais configurables entre les requêtes
- Gestion des quotas et limites de taux
- Implémentation de backoff exponentiel en cas d'erreur

### Qualité des Données
- Validation des données extraites
- Détection des doublons sophistiquée
- Nettoyage automatique des caractères parasites

### Monitoring et Logging
- Logs détaillés pour le suivi des extractions
- Compteurs de progression en temps réel
- Alertes en cas d'erreur critique

## Limitations et Améliorations Futures

### Limitations Actuelles
- Dépendance aux APIs externes et leurs limitations
- Temps de traitement important pour les grandes extractions
- Qualité variable selon les sources de données

### Améliorations Envisagées
- Mise en cache intelligente pour réduire les requêtes
- Parallélisation des extractions
- Interface utilisateur pour le monitoring
- Export vers d'autres formats (CSV, JSON, XML)

## Maintenance et Support

Ce module nécessite une maintenance régulière pour :
- Adapter aux changements des APIs externes
- Optimiser les performances selon l'usage
- Mettre à jour les algorithmes de nettoyage
- Ajouter le support de nouvelles sources de données

## Contexte du Stage

Ce travail s'inscrit dans le cadre d'un stage visant à développer un système complet d'analyse bibliographique. L'objectif est de créer une plateforme permettant aux chercheurs et institutions de suivre et analyser la production scientifique de manière automatisée et exhaustive.