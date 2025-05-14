#!/usr/bin/env python
# verification_mongodb.py - Script pour tester la connexion MongoDB

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Afficher les variables d'environnement
print("Variables d'environnement:")
print(f"MONGO_URI = {os.environ.get('MONGO_URI', 'Non défini')}")

# Tester avec l'URI de la variable d'environnement
try:
    uri_env = os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/Donnees')
    print(f"\nTest de connexion avec URI de l'environnement: {uri_env}")
    client_env = MongoClient(uri_env, serverSelectionTimeoutMS=5000)
    client_env.admin.command('ping')
    print("✅ Connexion réussie avec l'URI de l'environnement")
except Exception as e:
    print(f"❌ Échec de la connexion avec l'URI de l'environnement: {e}")

# Tester avec localhost (devrait échouer dans Docker)
try:
    print("\nTest de connexion avec localhost (pour diagnostiquer le problème)")
    client_local = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
    client_local.admin.command('ping')
    print("✅ Connexion réussie à localhost (inattendu dans Docker)")
except Exception as e:
    print(f"❌ Échec de la connexion à localhost (attendu dans Docker): {e}")

# Tester avec le nom de service MongoDB
try:
    print("\nTest de connexion avec le nom du service: mongodb:27017")
    client_service = MongoClient('mongodb://mongodb:27017/', serverSelectionTimeoutMS=5000)
    client_service.admin.command('ping')
    print("✅ Connexion réussie avec le nom du service")
except Exception as e:
    print(f"❌ Échec de la connexion avec le nom du service: {e}")

# Test d'import de la configuration
print("\nTest d'import de la configuration:")
try:
    sys.path.append('/app')  # Pour s'assurer que config.py est dans le chemin
    from config import MONGO_URI, MONGO_DB_NAME
    print(f"✅ Import de config.py réussi. MONGO_URI = {MONGO_URI}, DB_NAME = {MONGO_DB_NAME}")
    
    # Tester la connexion avec l'URI du fichier config
    client_config = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client_config.admin.command('ping')
    print(f"✅ Connexion réussie avec MONGO_URI de config.py")
except ImportError:
    print("❌ Échec d'import de config.py")
except Exception as e:
    print(f"❌ Échec de connexion avec MONGO_URI de config.py: {e}")

print("\n=== Test terminé ===")