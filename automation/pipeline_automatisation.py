"""
pipeline_automatisation.py - Script principal pour la gestion du pipeline d'automatisation
Ce script configure et orchestre les différentes composantes du système d'automatisation
pour la mise à jour des publications et l'amélioration continue du modèle de recommandation.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import json
import pickle
import pandas as pd
import numpy as np
import requests
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline_auto.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Chemins du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "model_cache")
CONFIG_PATH = os.path.join(BASE_DIR, "config.py")
LOGS_DIR = os.path.join(MODEL_DIR, "logs")
FEEDBACK_DIR = os.path.join(MODEL_DIR, "feedback")

# S'assurer que les répertoires existent
for directory in [MODEL_DIR, LOGS_DIR, FEEDBACK_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Répertoire créé: {directory}")

# Importer la configuration
sys.path.append(BASE_DIR)
import config

# Importer le modèle de recommandation
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from Modele.Modele_basé_sur_contenu.modele import DomainBasedRecommender    
    logger.info("Module de recommandation importé avec succès")
except ImportError as e:
    logger.error(f"Erreur lors de l'importation du module de recommandation: {e}")
    sys.exit(1)

class AutomationPipeline:
    """Classe gérant le pipeline d'automatisation pour le système de recommandation"""
    
    def __init__(self):
        """Initialisation du pipeline d'automatisation"""
        self.recommender = DomainBasedRecommender()
        
        # Configuration de MLflow
        try:
            mlflow.set_tracking_uri("http://localhost:5000")
            mlflow.set_experiment("automation_pipeline")
            self.mlflow_client = MlflowClient()
            logger.info("MLflow initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de MLflow: {e}")
        
        # Vérifier si le modèle est déjà construit
        self.check_model_status()
    
    def check_model_status(self):
        """Vérifie l'état du modèle et le charge si disponible"""
        vectorizer_path = os.path.join(MODEL_DIR, "vectorizer.pkl")
        vectors_path = os.path.join(MODEL_DIR, "publication_vectors.pkl")
        publications_path = os.path.join(MODEL_DIR, "publications_df.pkl")
        
        if (os.path.exists(vectorizer_path) and 
            os.path.exists(vectors_path) and 
            os.path.exists(publications_path)):
            
            logger.info("Modèle trouvé dans le cache, chargement...")
            try:
                with open(vectorizer_path, 'rb') as f:
                    self.recommender.vectorizer = pickle.load(f)
                
                with open(vectors_path, 'rb') as f:
                    self.recommender.publication_vectors = pickle.load(f)
                    
                with open(publications_path, 'rb') as f:
                    self.recommender.publications_df = pickle.load(f)
                    
                logger.info("Modèle chargé avec succès")
                return True
            except Exception as e:
                logger.error(f"Erreur lors du chargement du modèle: {e}")
                return False
        else:
            logger.info("Modèle non trouvé dans le cache")
            return False
    
    def update_publications(self):
        """Met à jour les publications dans la base de données"""
        logger.info("Mise à jour des publications en cours...")
        
        try:
            # Se connecter à MongoDB
            from pymongo import MongoClient
            client = MongoClient(config.MONGO_URI)
            db = client[config.MONGO_DB_NAME]
            publications_collection = db[config.COLLECTIONS["publications"]]
            
            # Dans une implémentation réelle, récupérer les nouvelles publications 
            # depuis une source externe (API, web scraping, etc.)
            # Ici, nous simulons l'ajout de nouvelles publications
            
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
            
            # En mode production, ajouter les publications à la base de données
            if not config.TEST_MODE:
                result = publications_collection.insert_many(new_publications)
                logger.info(f"Ajout de {len(result.inserted_ids)} nouvelles publications à la base de données")
            else:
                logger.info("Mode TEST: Simulation d'ajout de publications")
            
            # Signaler que le modèle doit être mis à jour
            with open(os.path.join(MODEL_DIR, "update_needed.flag"), "w") as f:
                f.write("1")
            
            logger.info(f"Mise à jour terminée avec {len(new_publications)} nouvelles publications")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des publications: {e}")
            return False
    
    def refresh_model(self):
        """Met à jour le modèle de recommandation avec les nouvelles publications"""
        logger.info("Rafraîchissement du modèle en cours...")
        
        try:
            with mlflow.start_run(run_name=f"model_refresh_{datetime.now().strftime('%Y%m%d')}"):
                # Initialiser le recommandeur
                if not self.recommender:
                    self.recommender = DomainBasedRecommender()
                
                # Charger les publications depuis la base de données
                self.recommender.load_publications()
                self.recommender.prepare_publications()
                
                # Construire le modèle
                self.recommender.build_model()
                
                # Enregistrer les métriques du modèle
                mlflow.log_metric("nb_publications", len(self.recommender.publications_df))
                if hasattr(self.recommender.vectorizer, 'max_features'):
                    mlflow.log_metric("vectorizer_features", self.recommender.vectorizer.max_features)
                
                # Sauvegarder le modèle mis à jour
                vectorizer_path = os.path.join(MODEL_DIR, "vectorizer.pkl")
                vectors_path = os.path.join(MODEL_DIR, "publication_vectors.pkl")
                publications_path = os.path.join(MODEL_DIR, "publications_df.pkl")
                
                with open(vectorizer_path, 'wb') as f:
                    pickle.dump(self.recommender.vectorizer, f)
                    
                with open(vectors_path, 'wb') as f:
                    pickle.dump(self.recommender.publication_vectors, f)
                    
                with open(publications_path, 'wb') as f:
                    pickle.dump(self.recommender.publications_df, f)
                    
                # Enregistrer le modèle dans MLflow
                mlflow.sklearn.log_model(self.recommender.vectorizer, "vectorizer")
                
                # Supprimer le drapeau de mise à jour
                update_flag_path = os.path.join(MODEL_DIR, "update_needed.flag")
                if os.path.exists(update_flag_path):
                    os.remove(update_flag_path)
                
                logger.info("Modèle rafraîchi avec succès")
                return True
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement du modèle: {e}")
            return False
    
    def analyze_user_feedback(self):
        """Analyse les retours utilisateurs et génère des métriques"""
        logger.info("Analyse des retours utilisateurs en cours...")
        
        try:
            # Récupérer tous les fichiers de feedback des dernières 24 heures
            feedback_files = []
            yesterday = datetime.now() - timedelta(days=1)
            
            for filename in os.listdir(FEEDBACK_DIR):
                if filename.endswith('.json'):
                    file_path = os.path.join(FEEDBACK_DIR, filename)
                    file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mod_time >= yesterday:
                        feedback_files.append(file_path)
            
            # Charger et analyser les feedbacks
            all_feedbacks = []
            for file_path in feedback_files:
                try:
                    with open(file_path, 'r') as f:
                        feedbacks = json.load(f)
                        if isinstance(feedbacks, list):
                            all_feedbacks.extend(feedbacks)
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier {file_path}: {e}")
            
            # Si aucun feedback n'est disponible
            if not all_feedbacks:
                logger.info("Aucun retour utilisateur disponible pour analyse")
                return False
            
            # Analyser les feedbacks
            df_feedback = pd.DataFrame(all_feedbacks)
            
            # Calculer les métriques
            metrics = {
                "total_feedbacks": len(df_feedback),
                "average_rating": df_feedback['rating'].mean() if 'rating' in df_feedback.columns else 0,
                "median_rating": df_feedback['rating'].median() if 'rating' in df_feedback.columns else 0,
                "unique_users": df_feedback['user'].nunique() if 'user' in df_feedback.columns else 0
            }
            
            # Enregistrer les métriques avec MLflow
            with mlflow.start_run(run_name=f"feedback_analysis_{datetime.now().strftime('%Y%m%d')}"):
                for key, value in metrics.items():
                    mlflow.log_metric(key, value)
                
                # Sauvegarder les métriques dans un fichier
                metrics_path = os.path.join(MODEL_DIR, "feedback_metrics.json")
                with open(metrics_path, 'w') as f:
                    json.dump(metrics, f)
            
            logger.info(f"Analyse des retours utilisateurs terminée: {metrics}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des retours utilisateurs: {e}")
            return False
    
    def optimize_model_based_on_feedback(self):
        """Optimise le modèle en fonction des retours utilisateurs"""
        logger.info("Optimisation du modèle en cours...")
        
        # Vérifier si des métriques de feedback sont disponibles
        metrics_path = os.path.join(MODEL_DIR, "feedback_metrics.json")
        if not os.path.exists(metrics_path):
            logger.info("Aucune métrique de feedback disponible, optimisation annulée")
            return False
        
        try:
            # Charger les métriques de feedback
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            
            # Vérifier si nous devons optimiser le modèle
            # Par exemple, si la note moyenne est inférieure à 3.5
            if metrics.get('average_rating', 5) < 3.5 and metrics.get('total_feedbacks', 0) > 10:
                logger.info("Optimisation du modèle nécessaire")
                
                # Dans une implémentation réelle, ajuster les paramètres du modèle
                # Par exemple, modifier les poids des features, ajuster les seuils, etc.
                
                with mlflow.start_run(run_name=f"model_optimization_{datetime.now().strftime('%Y%m%d')}"):
                    # Log des paramètres d'optimisation
                    mlflow.log_param("optimization_trigger", "low_rating")
                    mlflow.log_param("average_rating", metrics.get('average_rating', 0))
                    mlflow.log_param("feedback_count", metrics.get('total_feedbacks', 0))
                    
                    # Exemple d'optimisation: rechargement complet du modèle
                    return self.refresh_model()
            else:
                logger.info("Pas d'optimisation nécessaire selon les métriques de feedback actuelles")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation du modèle: {e}")
            return False
    
    def monitor_api_health(self):
        """Vérifie l'état de l'API de recommandation"""
        logger.info("Vérification de l'état de l'API...")
        
        try:
            # Appeler le endpoint de santé de l'API
            response = requests.get("http://localhost:5000/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                
                with mlflow.start_run(run_name=f"api_health_check_{datetime.now().strftime('%Y%m%d')}"):
                    mlflow.log_param("api_status", health_data.get("status", "unknown"))
                    mlflow.log_metric("response_time_ms", response.elapsed.total_seconds() * 1000)
                
                logger.info(f"API en bon état: {health_data}")
                return True
            else:
                logger.warning(f"API en état dégradé: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la vérification de l'API: {e}")
            return False
    
    def run_complete_pipeline(self):
        """Exécute l'ensemble du pipeline d'automatisation"""
        logger.info("Exécution du pipeline complet...")
        
        # 1. Mettre à jour les publications
        update_success = self.update_publications()
        if not update_success:
            logger.error("Échec de la mise à jour des publications")
        
        # 2. Rafraîchir le modèle si nécessaire
        update_flag_path = os.path.join(MODEL_DIR, "update_needed.flag")
        if os.path.exists(update_flag_path):
            refresh_success = self.refresh_model()
            if not refresh_success:
                logger.error("Échec du rafraîchissement du modèle")
        
        # 3. Analyser les retours utilisateurs
        analysis_success = self.analyze_user_feedback()
        if not analysis_success:
            logger.warning("Pas de retours utilisateurs à analyser ou erreur d'analyse")
        
        # 4. Optimiser le modèle en fonction des retours
        optimization_success = self.optimize_model_based_on_feedback()
        if not optimization_success:
            logger.warning("Pas d'optimisation effectuée ou erreur d'optimisation")
        
        # 5. Vérifier l'état de l'API
        api_health = self.monitor_api_health()
        if not api_health:
            logger.error("L'API semble être en panne ou dégradée")
        
        logger.info("Pipeline d'automatisation terminé")

if __name__ == "__main__":
    """Point d'entrée pour l'exécution manuelle du pipeline"""
    pipeline = AutomationPipeline()
    pipeline.run_complete_pipeline()