from mongo_connector import MongoConnector # type: ignore
from config import COLLECTIONS
import pandas as pd
import re 

class ScholarRepository:
    def __init__(self):
        self.connector = MongoConnector()
        self.connector.connect()
    
    def save_researcher(self, researcher_data):
        """Enregistre un chercheur dans la base de données"""
        collection = self.connector.get_collection(COLLECTIONS["chercheurs"])
        return collection.insert_one(researcher_data).inserted_id
    
    def save_publications(self, publications_data):
        """Enregistre une liste de publications dans la base de données"""
        collection = self.connector.get_collection(COLLECTIONS["publications"])
        if publications_data:
            return collection.insert_many(publications_data).inserted_ids
        return []
    
    def update_publication(self, pub_id, update_data):
        """Met à jour une publication"""
        collection = self.connector.get_collection(COLLECTIONS["publications"])
        return collection.update_one({"_id": pub_id}, {"$set": update_data})
    
    def save_statistics(self, stats_data):
        """Enregistre des statistiques"""
        collection = self.connector.get_collection(COLLECTIONS["stats"])
        return collection.insert_one(stats_data).inserted_id
    
    def get_researcher_publications(self, researcher_id):
        """Récupère toutes les publications d'un chercheur"""
        collection = self.connector.get_collection(COLLECTIONS["publications"])
        return list(collection.find({"chercheur_id": researcher_id}))
    def find_researcher_by_name(self, name):
        """Recherche un chercheur par son nom dans la base de données, en tenant compte des variations"""
        collection = self.connector.get_collection(COLLECTIONS["chercheurs"])
        
        # Nettoyage et normalisation du nom
        clean_name = name.strip().lower()
        
        # Décomposer le nom en mots individuels
        name_parts = [part for part in re.split(r'\s+', clean_name) if part]
        
        # Créer des variations possibles (nom prénom, prénom nom)
        queries = []
        
        # Recherche exacte (insensible à la casse)
        queries.append({"nom": {"$regex": f"^{re.escape(clean_name)}$", "$options": "i"}})
        
        # Si nous avons au moins 2 parties (prénom nom ou nom prénom)
        if len(name_parts) >= 2:
            # Variation 1: premier mot comme prénom, reste comme nom
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:])
            queries.append({
                "$or": [
                    {"nom": {"$regex": f"^{re.escape(last_name)}\\s+{re.escape(first_name)}$", "$options": "i"}},
                    {"nom": {"$regex": f"^{re.escape(first_name)}\\s+{re.escape(last_name)}$", "$options": "i"}}
                ]
            })
            
            # Variation 2: dernier mot comme nom, reste comme prénom
            first_name = " ".join(name_parts[:-1])
            last_name = name_parts[-1]
            queries.append({
                "$or": [
                    {"nom": {"$regex": f"^{re.escape(last_name)}\\s+{re.escape(first_name)}$", "$options": "i"}},
                    {"nom": {"$regex": f"^{re.escape(first_name)}\\s+{re.escape(last_name)}$", "$options": "i"}}
                ]
            })
        
        # Combiner toutes les requêtes avec un $or
        combined_query = {"$or": queries}
        
        return collection.find_one(combined_query)
    
    def update_researcher(self, researcher_id, update_data):
        """Met à jour les informations d'un chercheur"""
        collection = self.connector.get_collection(COLLECTIONS["chercheurs"])
        return collection.update_one({"_id": researcher_id}, {"$set": update_data})
    def find_similar_publication(self, chercheur_id, title, year=None):
        """Recherche une publication similaire basée sur le titre et l'année"""
        collection = self.connector.get_collection(COLLECTIONS["publications"])
        
        # Créer une requête de base avec l'ID du chercheur
        query = {"chercheur_id": chercheur_id}
        
        # Ajouter une recherche insensible à la casse sur le titre
        if title:
            # Vérifier si title est une liste et prendre le premier élément dans ce cas
            if isinstance(title, list):
                clean_title = title[0].strip().lower() if title else ""
            else:
                clean_title = title.strip().lower()
                
            # Utiliser une expression régulière pour rechercher un titre similaire
            query["title"] = {"$regex": f".*{re.escape(clean_title[:50])}.*", "$options": "i"}
        
        # Ajouter l'année si disponible
        if year:
            query["year"] = year
        
        return collection.find_one(query)
    def find_similar_publication_by_title(self, title, year=None):
        """Recherche une publication similaire basée sur le titre et l'année, sans chercheur_id"""
        collection = self.connector.get_collection(COLLECTIONS["publications"])
        
        # Créer une requête de base
        query = {}
        
        # Ajouter une recherche insensible à la casse sur le titre
        if title:
            # Vérifier si title est une liste et prendre le premier élément dans ce cas
            if isinstance(title, list):
                clean_title = title[0].strip().lower() if title else ""
            else:
                clean_title = title.strip().lower()
                
            # Utiliser une expression régulière pour rechercher un titre similaire
            query["title"] = {"$regex": f".*{re.escape(clean_title[:50])}.*", "$options": "i"}
        
        # Ajouter l'année si disponible
        if year:
            query["year"] = year
        
        return collection.find_one(query)
    def close(self):
        """Ferme la connexion à la base de données"""
        self.connector.close()