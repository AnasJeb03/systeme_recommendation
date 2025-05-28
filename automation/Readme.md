# Pipeline d'Automatisation - Système de Recommandation

## 📋 Vue d'ensemble

Ce module gère l'automatisation complète du système de recommandation de publications scientifiques. Il orchestre la mise à jour des données, l'amélioration continue du modèle et le monitoring des performances grâce à un pipeline robuste et scalable.

## 🏗️ Architecture

### Composants principaux

- **`pipeline_automatisation.py`** : Script principal orchestrant l'ensemble du pipeline
- **`recommendation_dags.py`** : Configuration des DAGs Apache Airflow pour la planification des tâches
- **MLflow** : Suivi des expériences et versioning des modèles
- **MongoDB** : Base de données pour les publications et l'historique des recherches

### Flux de données

```
Nouvelles Publications → Mise à jour BD → Rafraîchissement Modèle
                                      ↘
Feedback Utilisateurs → Analyse Métriques → Optimisation Modèle
                                      ↘
                              Monitoring API → Alertes
```

## 🚀 Installation et Configuration

### Prérequis

```bash
# Dépendances Python
pip install apache-airflow mlflow pymongo pandas numpy scikit-learn requests

# Services externes
docker run -d -p 5000:5000 --name mlflow-server mlflow server --host 0.0.0.0
```

### Configuration des répertoires

Le pipeline crée automatiquement les répertoires suivants :
- `model_cache/` : Cache des modèles entraînés
- `model_cache/logs/` : Journaux d'exécution
- `model_cache/feedback/` : Données de retour utilisateur

### Variables d'environnement

Assurez-vous que votre fichier `config.py` contient :

```python
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "recommendation_db"
COLLECTIONS = {
    "publications": "publications",
    "search_history": "SearchHistory"
}
TEST_MODE = False  # True pour les tests
```

## 📊 Fonctionnalités

### 1. Mise à jour automatique des publications

```python
# Exécution manuelle
pipeline = AutomationPipeline()
pipeline.update_publications()
```

**Fonctionnalités :**
- Récupération de nouvelles publications depuis sources externes
- Insertion en base de données MongoDB  
- Déclenchement automatique du rafraîchissement du modèle

### 2. Rafraîchissement du modèle

**Processus automatisé :**
- Rechargement des publications depuis la BD
- Reconstruction des vecteurs TF-IDF
- Mise en cache du modèle optimisé
- Enregistrement des métriques dans MLflow

### 3. Analyse des retours utilisateurs

**Métriques collectées :**
- Nombre total de feedbacks
- Note moyenne des recommandations
- Nombre d'utilisateurs uniques
- Tendances par domaine de recherche

### 4. Optimisation basée sur les performances

Le système adapte automatiquement les paramètres du modèle selon :
- Les notes utilisateurs (seuil < 3.5/5)
- Le volume de feedback (minimum 10 retours)
- Les métriques de performance

### 5. Monitoring de l'API

Surveillance continue de :
- Disponibilité du service (endpoint `/health`)
- Temps de réponse
- Métriques de performance

## 🔄 Orchestration avec Apache Airflow

### DAGs configurés

#### 1. `update_publications_daily`
- **Fréquence** : Quotidienne
- **Fonction** : Mise à jour des publications
- **Retry** : 1 tentative avec délai de 5 minutes

#### 2. `refresh_model_weekly`  
- **Fréquence** : Hebdomadaire
- **Fonction** : Rafraîchissement complet du modèle
- **Suivi** : Métriques MLflow automatiques

#### 3. `monitor_model_performance`
- **Fréquence** : Quotidienne  
- **Fonction** : Collecte feedback + optimisation
- **Pipeline** : `collect_user_feedback` → `optimize_model`

### Démarrage d'Airflow

```bash
# Initialiser la base de données Airflow
airflow db init

# Créer un utilisateur admin
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com

# Démarrer le scheduler et le webserver
airflow scheduler &
airflow webserver --port 8080
```

Interface web accessible sur : `http://localhost:8080`

## 📈 Monitoring avec MLflow

### Accès à l'interface

```bash
mlflow ui --host 0.0.0.0 --port 5000
```

Interface web : `http://localhost:5000`

### Expériences trackées

- **`automation_pipeline`** : Métriques générales du pipeline
- **`recommandation_publications`** : Performance du modèle
- **`recommandation_feedback`** : Analyse des retours utilisateurs
- **`recommandation_optimisation`** : Optimisations appliquées

### Métriques clés

- Nombre de publications traitées
- Précision du modèle de recommandation
- Satisfaction utilisateur moyenne
- Temps de réponse API

## 🔧 Utilisation

### Exécution complète du pipeline

```python
from pipeline_automatisation import AutomationPipeline

# Initialisation
pipeline = AutomationPipeline()

# Exécution complète
pipeline.run_complete_pipeline()
```

### Exécution de tâches spécifiques

```python
# Mise à jour des publications uniquement
pipeline.update_publications()

# Rafraîchissement du modèle
pipeline.refresh_model()

# Analyse des feedbacks
pipeline.analyze_user_feedback()

# Optimisation
pipeline.optimize_model_based_on_feedback()

# Vérification API
pipeline.monitor_api_health()
```

### Mode de test

Pour les environnements de développement :

```python
# Dans config.py
TEST_MODE = True
```

En mode test, aucune donnée n'est écrite en base de données.

## 📁 Structure des fichiers

```
automation/
├── pipeline_automatisation.py    # Pipeline principal
├── recommendation_dags.py        # Configuration Airflow
├── model_cache/                  # Cache modèles
│   ├── vectorizer.pkl           # Vectoriseur TF-IDF
│   ├── publication_vectors.pkl  # Vecteurs publications  
│   ├── publications_df.pkl      # DataFrame publications
│   ├── feedback_metrics.json    # Métriques feedback
│   ├── logs/                    # Journaux
│   └── feedback/                # Données feedback
└── README.md                    # Documentation
```

## 🔍 Logging et Debugging

### Configuration des logs

Les logs sont automatiquement sauvegardés dans :
- Console : Niveau INFO
- Fichier : `pipeline_auto.log` (tous niveaux)

### Debugging des erreurs courantes

**Erreur de connexion MongoDB :**
```python
# Vérifier la connexion
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
client.admin.command('ping')  # Doit retourner {'ok': 1.0}
```

**Erreur MLflow :**
```bash
# Redémarrer le serveur MLflow
mlflow server --host 0.0.0.0 --port 5000
```

**Modèle non trouvé :**
```python
# Forcer la reconstruction
pipeline.refresh_model()
```

## 🚨 Monitoring et Alertes

### Indicateurs de santé

- ✅ **Vert** : Toutes les tâches s'exécutent normalement
- ⚠️ **Orange** : Avertissements (feedback insuffisant, API lente)
- ❌ **Rouge** : Erreurs critiques (API indisponible, échec modèle)

### Alertes configurées

- Email automatique en cas d'échec des DAGs Airflow
- Logging détaillé pour diagnostic
- Métriques MLflow pour suivi continu

## 🔄 Maintenance

### Tâches recommandées

**Quotidienne :**
- Vérification des logs d'erreur
- Contrôle des métriques MLflow

**Hebdomadaire :**
- Nettoyage des anciens logs
- Analyse des tendances de performance

**Mensuelle :**
- Optimisation de la base de données
- Révision des seuils d'alerte

### Mise à jour

Pour mettre à jour le pipeline :

1. Arrêter les services Airflow
2. Déployer les nouveaux fichiers
3. Redémarrer les services
4. Vérifier les DAGs dans l'interface web

## 📞 Support

En cas de problème :

1. Consulter les logs dans `pipeline_auto.log`
2. Vérifier l'interface MLflow pour les métriques
3. Contrôler les DAGs Airflow pour les échecs de tâches
4. Tester la connectivité MongoDB et API

## 🔮 Évolutions futures

- Intégration de sources de données supplémentaires
- Algorithmes de recommandation plus sophistiqués
- Tableau de bord temps réel pour le monitoring
- Tests d'A/B pour l'optimisation continue
- Scaling horizontal avec Kubernetes