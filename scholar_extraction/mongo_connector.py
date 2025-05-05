from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import sys
import os
import time
import logging

# Ajouter le répertoire parent au chemin pour importer config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MONGO_URI, MONGO_DB_NAME, COLLECTIONS

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MongoConnector:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoConnector, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.db = None
            cls._instance.max_retries = 5
            cls._instance.retry_delay = 3
        return cls._instance
    
    def connect(self):
        """Établit une connexion à MongoDB avec tentatives de reconnexion."""
        logger.info(f"Tentative de connexion avec URI: {MONGO_URI}")
        attempt = 0
        while attempt < self.max_retries:
            try:
                logger.info(f"Tentative de connexion à MongoDB ({attempt+1}/{self.max_retries})...")
                print(f"Tentative de connexion à MongoDB ({attempt+1}/{self.max_retries})...")
                
                # Augmenter le timeout pour donner plus de temps au service MongoDB de démarrer
                self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
                
                # Vérifier que la connexion fonctionne
                self.client.admin.command('ping')
                self.db = self.client[MONGO_DB_NAME]
                
                # Vérifier que les collections existent et les créer si nécessaire
                self._ensure_collections_exist()
                
                logger.info("Connexion à MongoDB établie avec succès!")
                print("Connexion à MongoDB établie avec succès!")
                return True
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                attempt += 1
                logger.error(f"Erreur de connexion à MongoDB: {str(e)}")
                print(f"Erreur de connexion à MongoDB: {str(e)}")
                
                if attempt < self.max_retries:
                    logger.info(f"Nouvelle tentative dans {self.retry_delay} secondes...")
                    print(f"Nouvelle tentative dans {self.retry_delay} secondes...")
                    time.sleep(self.retry_delay)
                    # Augmenter le délai progressivement
                    self.retry_delay *= 1.5
                else:
                    logger.error("Nombre maximum de tentatives atteint. Impossible de se connecter à MongoDB.")
                    print("Nombre maximum de tentatives atteint. Impossible de se connecter à MongoDB.")
                    return False
    
    def _ensure_collections_exist(self):
        """S'assure que toutes les collections nécessaires existent"""
        for collection_name in COLLECTIONS.values():
            if collection_name not in self.db.list_collection_names():
                logger.info(f"Création de la collection {collection_name}")
                print(f"Création de la collection {collection_name}")
                self.db.create_collection(collection_name)
    
    def get_collection(self, collection_name):
        """Obtient une collection avec vérification de connexion."""
        # Vérifier si la connexion existe
        if self.client is None or self.db is None:
            logger.info("Connexion à MongoDB non établie. Tentative de connexion...")
            reconnected = self.connect()
            if not reconnected:
                logger.error("ERREUR: Impossible d'accéder à la collection car la connexion à MongoDB a échoué.")
                print("ERREUR: Impossible d'accéder à la collection car la connexion à MongoDB a échoué.")
                return None
        
        try:
            # Vérifier que la connexion est toujours active
            self.client.admin.command('ping')
        except Exception as e:
            logger.error(f"La connexion à MongoDB a été perdue: {e}. Tentative de reconnexion...")
            print(f"La connexion à MongoDB a été perdue: {e}. Tentative de reconnexion...")
            reconnected = self.connect()
            if not reconnected:
                logger.error("ERREUR: Échec de la reconnexion à MongoDB.")
                print("ERREUR: Échec de la reconnexion à MongoDB.")
                return None
        
        # Maintenant, nous pouvons accéder à la collection
        if collection_name in COLLECTIONS.values():
            return self.db[collection_name]
        raise ValueError(f"Collection {collection_name} non définie dans la configuration.")
    
    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("Connexion à MongoDB fermée.")
            print("Connexion à MongoDB fermée.")