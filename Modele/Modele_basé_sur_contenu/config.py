import os
# Configuration MongoDB
MONGO_URI = "mongodb+srv://root:root@projet.orx8tzk.mongodb.net/"  
MONGO_DB_NAME = "Donnees"
COLLECTIONS = {
    "chercheurs": "auteurs",
    "publications": "Publications",
    "stats": "Statistiques"
}

# Mode test (utiliser True pour éviter les problèmes de connexion pendant le développement)
TEST_MODE = False  # Mettre à False pour utiliser la base de données réelle

# Paramètres d'extraction
MAX_AUTHORS_RESULTS = 5
MAX_PUBLICATIONS = None
SEARCH_DELAY = 1  # secondes entre les requêtes
# Configuration pour Semantic Scholar
SEMANTIC_SCHOLAR_API_KEY = None  # Insérez votre clé API ici si vous en avez une
SEMANTIC_SCHOLAR_MAX_RESULTS = 100  # Nombre maximum de résultats à récupérer