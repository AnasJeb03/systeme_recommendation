# Configuration globale pour tous les modules
import os

# Configuration MongoDB
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://root:root@projet.orx8tzk.mongodb.net/')
MONGO_DB_NAME = 'Donnees'

# Définir les collections
COLLECTIONS = {
    'PUBLICATIONS': 'publications',
    'AUTEURS': 'auteurs',
    'RECOMMENDATIONS': 'recommendations'
}

# Configuration des chemins
BASE_DIR = '/app'
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_CACHE_DIR = os.path.join(BASE_DIR, 'model_cache')

# Configuration Airflow
AIRFLOW_HOME = os.environ.get('AIRFLOW_HOME', '/app/airflow')

# Autres configurations
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
RETRY_ATTEMPTS = 5
RETRY_DELAY = 5  # secondes

# Configuration spécifique au modèle
MODEL_PARAMETERS = {
    'vectorizer': 'tfidf',  # Options: 'tfidf', 'count', 'bert'
    'top_n': 10,  # Nombre de recommandations à générer
    'similarity_threshold': 0.3  # Seuil minimal de similarité
}

# Mode de fonctionnement
# Si TEST_MODE est activé, le système utilisera des données de test en cas d'échec de connexion à MongoDB
TEST_MODE = os.environ.get('TEST_MODE', 'True').lower() == 'true'