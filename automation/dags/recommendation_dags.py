from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import requests
import os
import sys
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from pymongo import MongoClient
import json
import pickle

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Modele.Modele_basé_sur_contenu.modele import DomainBasedRecommender    
import config

# Configuration des chemins pour le cache du modèle
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model_cache")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")
VECTORS_PATH = os.path.join(MODEL_DIR, "publication_vectors.pkl")
PUBLICATIONS_PATH = os.path.join(MODEL_DIR, "publications_df.pkl")
FEEDBACK_PATH = os.path.join(MODEL_DIR, "user_feedback.json")

# Paramètres par défaut pour les DAGs Airflow
default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Créer un DAG pour la mise à jour quotidienne des publications
dag_update_publications = DAG(
    'update_publications_daily',
    default_args=default_args,
    description='Mise à jour quotidienne des publications scientifiques',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
    tags=['recommandation', 'publications'],
)

# Fonction pour mettre à jour les publications dans la base de données
def update_publications():
    """Récupère les nouvelles publications et les ajoute à la base de données MongoDB"""
    print("Mise à jour des publications en cours...")
    
    # Se connecter à MongoDB
    client = MongoClient(config.MONGO_URI)
    db = client[config.MONGO_DB_NAME]
    publications_collection = db[config.COLLECTIONS["publications"]]
    
    # Code pour récupérer les nouvelles publications
    # Cette partie dépend de la source de vos données (API, scraping, etc.)
    # Pour cet exemple, nous simulerons l'ajout de quelques publications test
    
    new_publications = [
        {
            "title": f"Nouvelle publication sur l'IA - {datetime.now().strftime('%Y-%m-%d')}",
            "abstract_full": "Ceci est un résumé détaillé sur les avancées récentes en intelligence artificielle.",
            "abstract_short": "Résumé court sur l'IA.",
            "keywords": ["intelligence artificielle", "deep learning", "machine learning"],
            "url": "https://example.com/pub1",
            "date_added": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        },
        {
            "title": f"Avancées en traitement du langage naturel - {datetime.now().strftime('%Y-%m-%d')}",
            "abstract_full": "Cette publication explore les récentes avancées en NLP et leur application.",
            "abstract_short": "Étude sur le NLP.",
            "keywords": ["NLP", "traitement du langage", "transformers"],
            "url": "https://example.com/pub2",
            "date_added": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }
    ]
    
    # Ajouter les nouvelles publications à la base de données
    if not config.TEST_MODE:
        result = publications_collection.insert_many(new_publications)
        print(f"Ajout de {len(result.inserted_ids)} nouvelles publications à la base de données")
    else:
        print("Mode TEST: Simulation d'ajout de publications")
    
    # Signaler que le modèle doit être mis à jour
    with open(os.path.join(MODEL_DIR, "update_needed.flag"), "w") as f:
        f.write("1")
    
    return f"Mise à jour terminée avec {len(new_publications)} nouvelles publications"

# Tâche Airflow pour la mise à jour des publications
task_update_publications = PythonOperator(
    task_id='update_publications',
    python_callable=update_publications,
    dag=dag_update_publications,
)

# Fonction pour rafraîchir le modèle avec les nouvelles données
def refresh_model():
    """Met à jour le modèle de recommandation avec les nouvelles publications"""
    print("Rafraîchissement du modèle en cours...")
    
    # Initialiser MLflow pour le suivi des métriques
    mlflow.set_tracking_uri("http://localhost:5000")  # URL du serveur MLflow
    mlflow.set_experiment("recommandation_publications")
    
    with mlflow.start_run(run_name=f"model_refresh_{datetime.now().strftime('%Y%m%d')}"):
        # Initialiser le recommandeur
        recommender = DomainBasedRecommender()
        
        # Charger les publications
        recommender.load_publications()
        recommender.prepare_publications()
        
        # Construire le modèle
        recommender.build_model()
        
        # Enregistrer les métriques du modèle (exemple simple)
        mlflow.log_metric("nb_publications", len(recommender.publications_df))
        mlflow.log_metric("vectorizer_features", recommender.vectorizer.max_features)
        
        # Sauvegarder le modèle mis à jour
        with open(VECTORIZER_PATH, 'wb') as f:
            pickle.dump(recommender.vectorizer, f)
            
        with open(VECTORS_PATH, 'wb') as f:
            pickle.dump(recommender.publication_vectors, f)
            
        with open(PUBLICATIONS_PATH, 'wb') as f:
            pickle.dump(recommender.publications_df, f)
            
        # Enregistrer le modèle dans MLflow
        mlflow.sklearn.log_model(recommender.vectorizer, "vectorizer")
        
        # Supprimer le drapeau de mise à jour
        if os.path.exists(os.path.join(MODEL_DIR, "update_needed.flag")):
            os.remove(os.path.join(MODEL_DIR, "update_needed.flag"))
    
    return "Modèle rafraîchi avec succès"

# DAG pour le rafraîchissement hebdomadaire du modèle
dag_refresh_model = DAG(
    'refresh_model_weekly',
    default_args=default_args,
    description='Rafraîchissement hebdomadaire du modèle de recommandation',
    schedule_interval=timedelta(weeks=1),
    start_date=days_ago(1),
    tags=['recommandation', 'modèle'],
)

# Tâche Airflow pour le rafraîchissement du modèle
task_refresh_model = PythonOperator(
    task_id='refresh_model',
    python_callable=refresh_model,
    dag=dag_refresh_model,
)

# DAG pour le monitoring continu des performances du modèle
dag_monitor_model = DAG(
    'monitor_model_performance',
    default_args=default_args,
    description='Monitoring continu des performances du modèle',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
    tags=['recommandation', 'monitoring'],
)

# Fonction pour collecter et analyser les retours utilisateurs
def collect_user_feedback():
    """Collecte et analyse les retours utilisateurs sur les recommandations"""
    print("Collecte des retours utilisateurs en cours...")
    
    # Se connecter à MongoDB pour récupérer l'historique des recherches
    if not config.TEST_MODE:
        client = MongoClient(config.MONGO_URI)
        db = client[config.MONGO_DB_NAME]
        search_history_collection = db.get_collection("SearchHistory")
        
        # Récupérer les recherches des dernières 24 heures
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%dT%H:%M:%S")
        
        recent_searches = list(search_history_collection.find(
            {"timestamp": {"$gte": yesterday_str}}
        ))
        
        print(f"Nombre de recherches récentes: {len(recent_searches)}")
    else:
        # Mode test
        recent_searches = []
        print("Mode TEST: Simulation de l'analyse des retours utilisateurs")
    
    # Simuler l'analyse des retours utilisateurs
    # Dans une implémentation réelle, on analyserait les clics, temps passé, etc.
    feedback_metrics = {
        "total_searches": len(recent_searches),
        "avg_recommendations_clicked": 2.5,  # Simulé
        "avg_recommendation_relevance": 0.85,  # Simulé
        "domains_searched": ["intelligence artificielle", "machine learning", "data science"]  # Simulé
    }
    
    # Enregistrer les métriques dans MLflow
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("recommandation_feedback")
    
    with mlflow.start_run(run_name=f"user_feedback_{datetime.now().strftime('%Y%m%d')}"):
        for key, value in feedback_metrics.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(key, value)
        
        # Enregistrer les métriques également sur disque
        with open(FEEDBACK_PATH, 'w') as f:
            json.dump(feedback_metrics, f)
    
    return "Analyse des retours utilisateurs terminée"

# Tâche Airflow pour la collecte des retours utilisateurs
task_collect_feedback = PythonOperator(
    task_id='collect_user_feedback',
    python_callable=collect_user_feedback,
    dag=dag_monitor_model,
)

# Fonction pour optimiser le modèle en fonction des retours
def optimize_model():
    """Optimise le modèle en fonction des retours utilisateurs"""
    print("Optimisation du modèle en cours...")
    
    # Vérifier si le fichier de feedback existe
    if not os.path.exists(FEEDBACK_PATH):
        print("Aucune donnée de feedback disponible")
        return "Pas d'optimisation nécessaire"
    
    # Charger les métriques de feedback
    with open(FEEDBACK_PATH, 'r') as f:
        feedback_metrics = json.load(f)
    
    # Charger le recommandeur actuel
    recommender = DomainBasedRecommender()
    
    # Charger les données du cache
    with open(VECTORIZER_PATH, 'rb') as f:
        recommender.vectorizer = pickle.load(f)
    
    with open(VECTORS_PATH, 'rb') as f:
        recommender.publication_vectors = pickle.load(f)
        
    with open(PUBLICATIONS_PATH, 'rb') as f:
        recommender.publications_df = pickle.load(f)
    
    # Simuler l'optimisation du modèle basée sur les retours
    # Dans une implémentation réelle, on ajusterait les paramètres du modèle
    
    # Enregistrer les modifications dans MLflow
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("recommandation_optimisation")
    
    with mlflow.start_run(run_name=f"model_optimization_{datetime.now().strftime('%Y%m%d')}"):
        mlflow.log_param("feedback_based_optimization", True)
        mlflow.log_metric("expected_improvement", 0.05)  # Simulé
        
        # Sauvegarder le modèle "optimisé"
        with open(VECTORIZER_PATH, 'wb') as f:
            pickle.dump(recommender.vectorizer, f)
            
        with open(VECTORS_PATH, 'wb') as f:
            pickle.dump(recommender.publication_vectors, f)
    
    return "Optimisation du modèle terminée"

# Tâche Airflow pour l'optimisation du modèle
task_optimize_model = PythonOperator(
    task_id='optimize_model',
    python_callable=optimize_model,
    dag=dag_monitor_model,
)

# Définir l'ordre des tâches
task_collect_feedback >> task_optimize_model