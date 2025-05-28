import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from pymongo import MongoClient
from bson.objectid import ObjectId
import sys
import os
import re
import time
from datetime import datetime

# Importer la configuration
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

# Configuration de NLTK
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
stop_words = set(stopwords.words('french') + stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# Fonction de tokenization simplifiée pour éviter l'erreur punkt_tab
def simple_tokenize(text):
    # Convertir en minuscules et segmenter par espaces
    # Puis nettoyer pour ne garder que les caractères alphabétiques
    words = []
    if isinstance(text, str):
        # Séparer par espaces et filtrer les caractères non-alphabétiques
        for word in text.lower().split():
            # Filtrer pour ne garder que les lettres
            word = re.sub(r'[^a-zA-Z]', '', word)
            if word:  # S'assurer que le mot n'est pas vide
                words.append(word)
    return words

class DomainBasedRecommender:
    def __init__(self):
        # Connexion à MongoDB en utilisant le fichier de configuration
        try:
            self.client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
            if not config.TEST_MODE:
                # Vérifier la connexion
                self.client.server_info()
                self.db = self.client[config.MONGO_DB_NAME]
                
                # Accès aux collections
                self.chercheurs_collection = self.db[config.COLLECTIONS["chercheurs"]]
                self.publications_collection = self.db[config.COLLECTIONS["publications"]]
                self.stats_collection = self.db[config.COLLECTIONS["stats"]]
                
                # Collection pour stocker l'historique des recherches et recommandations
                self.search_history_collection = self.db.get_collection("SearchHistory")
                if self.search_history_collection is None:
                    self.db.create_collection("SearchHistory")
                    self.search_history_collection = self.db["SearchHistory"]
                
                print("Connexion à MongoDB réussie!")
            else:
                print("Mode TEST activé: utilisation de données simulées")
                # En mode test, on utilisera des variables locales
                self.db = None
                self.chercheurs_collection = []
                self.publications_collection = []
                self.stats_collection = []
                self.search_history_collection = []
                
        except Exception as e:
            print(f"Erreur de connexion à MongoDB: {e}")
            print("Passage en mode test pour le développement.")
            # En cas d'erreur, on passe automatiquement en mode test
            self.db = None
            self.chercheurs_collection = []
            self.publications_collection = []
            self.stats_collection = []
            self.search_history_collection = []
        
        # Initialisation des DataFrames
        self.publications_df = None
        self.vectorizer = None
        self.publication_vectors = None
        
        # Dictionnaire pour stocker les doctorants en mode test
        self.test_doctorants = {}
        # Liste pour stocker l'historique des recherches en mode test
        self.test_search_history = []

        
    def load_publications(self):
        """Charge les publications depuis MongoDB ou utilise des données de test"""
        print("Chargement des publications...")
        
        if config.TEST_MODE or self.db is None:
            # Utiliser des données de test
            self.load_test_data()
            return
            
        try:
            # Vérifier que la collection n'est pas vide
            try:
                count = self.publications_collection.count_documents({}, limit=1)
                if count == 0:
                    print("La collection de publications est vide, utilisation de données de test.")
                    self.load_test_data()
                    return
            except Exception as e:
                print(f"Erreur lors de la vérification de la collection: {e}")
                self.load_test_data()
                return
                
            # Récupérer avec une approche par lots (batching)
            batch_size = 2500
            total_documents = self.publications_collection.count_documents({})
            publications_list = []
            
            print(f"Début de la récupération de {total_documents} documents par lots de {batch_size}...")
            
            for skip in range(0, total_documents, batch_size):
                batch = self.publications_collection.find(
                    {}, 
                    {'_id': 1, 'title': 1, 'abstract_full': 1, 'abstract_short': 1, 'keywords': 1, 'url': 1}
                ).skip(skip).limit(batch_size)
                
                batch_list = list(batch)
                publications_list.extend(batch_list)
                print(f"Récupéré {len(publications_list)} documents sur {total_documents}...")
                
            if not publications_list:
                raise Exception("Aucune publication récupérée")
                
            self.publications_df = pd.DataFrame(publications_list)
            print(f"Publications chargées avec succès: {len(self.publications_df)} sur un total de {total_documents}")
            
        except Exception as e:
            print(f"Erreur lors du chargement des publications: {e}")
            # Utiliser des données de test en cas d'erreur
            self.load_test_data()
    def load_test_data(self):
        """
        Charge des données de test quand la connexion à MongoDB n'est pas disponible.
        Cette méthode est appelée en mode de secours quand load_publications() échoue.
        """
        import pandas as pd
        import os
        import logging
        
        # Configurer un logger si besoin
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('test_data_loader')
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        self.logger.info("Chargement des données de test pour le développement...")
        print("Chargement des données de test pour le développement...")
        
        # Créer un DataFrame avec quelques exemples de publications
        test_data = [
            {
                "_id": "test1",
                "title": "Introduction à l'apprentissage automatique",
                "abstract": "Cet article présente les concepts fondamentaux de l'apprentissage automatique et ses applications.",
                "authors": ["A. Smith", "B. Johnson"],
                "year": 2023,
                "keywords": ["machine learning", "AI", "data science"]
            },
            {
                "_id": "test2",
                "title": "Systèmes de recommandation basés sur le contenu",
                "abstract": "Étude des systèmes de recommandation utilisant la similarité de contenu pour proposer des items pertinents.",
                "authors": ["C. Williams", "D. Brown"],
                "year": 2022,
                "keywords": ["recommendation systems", "content-based filtering", "similarity measures"]
            },
            {
                "_id": "test3",
                "title": "Applications des réseaux de neurones",
                "abstract": "Analyse des applications pratiques des réseaux de neurones dans divers domaines industriels.",
                "authors": ["E. Davis", "F. Miller"],
                "year": 2024,
                "keywords": ["neural networks", "deep learning", "applications"]
            }
        ]
        
        # Convertir en DataFrame
        self.publications = pd.DataFrame(test_data)
        
        # Initialiser le vectorizer si nécessaire
        if not hasattr(self, 'vectorizer') or self.vectorizer is None:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(stop_words='english')
            # Construire le vectorizer avec les textes disponibles
            combined_texts = self.publications['title'] + " " + self.publications['abstract']
            self.vectorizer.fit(combined_texts)
        
        # S'assurer que la méthode index_publications existe
        if hasattr(self, 'index_publications'):
            # Vectoriser les textes
            self.index_publications()
        else:
            print("Avertissement: Méthode index_publications non disponible.")
        
        self.logger.info(f"Données de test chargées avec succès. {len(self.publications)} publications disponibles.")
        print(f"Données de test chargées avec succès. {len(self.publications)} publications disponibles.")  
    def preprocess_text(self, text):
            """Prétraite le texte: tokenization, suppression des stopwords, lemmatisation"""
            if isinstance(text, str):
                # Tokenisation simplifiée
                tokens = simple_tokenize(text)
                # Élimination des stopwords et lemmatisation
                tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
                return ' '.join(tokens)
            return ''    
        
    def keywords_to_text(self, keywords_list):
        """Convertit une liste de mots-clés en texte"""
        if isinstance(keywords_list, list):
            return ' '.join([str(keyword) for keyword in keywords_list])
        return ''
        
    def prepare_publications(self):
        """Prépare les publications pour le modèle de recommandation"""
        print("Préparation des publications...")
        
        if self.publications_df is None or len(self.publications_df) == 0:
            print("Aucune publication à préparer.")
            return
            
        if 'processed_text' not in self.publications_df.columns:
            self.publications_df['processed_text'] = ''
            
        for idx, row in self.publications_df.iterrows():
            # Concaténer titre et résumé
            title_text = self.preprocess_text(row.get('title', ''))
            abstract_text = self.preprocess_text(row.get('abstract_full', ''))
            
            # Traiter les mots-clés
            keywords = row.get('keywords', [])
            keywords_text = self.keywords_to_text(keywords)
            keywords_text = self.preprocess_text(keywords_text)
            
            # Concaténer tous les textes traités
            self.publications_df.at[idx, 'processed_text'] = f"{title_text} {abstract_text} {keywords_text}"
            
        print("Publications préparées avec succès")
        
    def build_model(self):
        """Construit le modèle TF-IDF et vectorise les publications"""
        print("Construction du modèle...")
        
        if self.publications_df is None or len(self.publications_df) == 0:
            print("Impossible de construire le modèle: aucune donnée disponible.")
            return
            
        if 'processed_text' not in self.publications_df.columns:
            print("Les publications doivent être préparées avant de construire le modèle.")
            self.prepare_publications()
            
        # Vectorisation TF-IDF pour les publications
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.publication_vectors = self.vectorizer.fit_transform(self.publications_df['processed_text'])
        print("Modèle construit avec succès")
        
    def find_or_create_doctorant(self, nom, email=None, interests=None):
        """Trouve un doctorant existant ou en crée un nouveau"""
        if self.db is None:
            # Mode test: gérer les doctorants en mémoire
            if nom in self.test_doctorants:
                return self.test_doctorants[nom]
                
            # Créer un nouveau profil de doctorant en mémoire avec un ObjectId valide
            import bson
            new_doctorant = {
                "_id": bson.ObjectId(),  # Génère un vrai ObjectId valide
                "nom": nom,
                "email": email,
                "interests": interests if interests else [],
                "affiliation": "",
                "h_index": 0,
                "i10_index": 0,
                "citations_total": 0,
                "date_creation": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            self.test_doctorants[nom] = new_doctorant
            print(f"Nouveau doctorant créé en mode test: {nom}")
            return new_doctorant
            
        # Mode normal: utiliser MongoDB
        # Chercher par nom
        doctorant = self.chercheurs_collection.find_one({"nom": nom})
        
        if doctorant is None and email:
            # Chercher par email si nom non trouvé
            doctorant = self.chercheurs_collection.find_one({"email": email})
            
        if doctorant is None:
            # Créer un nouveau profil de doctorant
            new_doctorant = {
                "nom": nom,
                "email": email,
                "interests": interests if interests else [],
                "affiliation": "",
                "h_index": 0,
                "i10_index": 0,
                "citations_total": 0,
                "date_creation": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            doctorant_id = self.chercheurs_collection.insert_one(new_doctorant).inserted_id
            doctorant = self.chercheurs_collection.find_one({"_id": doctorant_id})
            print(f"Nouveau doctorant créé: {nom}")
        
        return doctorant
        
    def update_doctorant_interests(self, doctorant_id, domain):
        """Met à jour les intérêts du doctorant avec le nouveau domaine"""
        if self.db is None:
            # Mode test: mettre à jour les intérêts en mémoire
            for doctorant_name, doctorant in self.test_doctorants.items():
                if doctorant["_id"] == doctorant_id:
                    interests = doctorant.get("interests", [])
                    if domain not in interests:
                        interests.append(domain)
                        doctorant["interests"] = interests
                        print(f"Intérêts mis à jour pour {doctorant.get('nom')} en mode test")
                    return
            return
                
        # Mode normal: utiliser MongoDB
        doctorant = self.chercheurs_collection.find_one({"_id": doctorant_id})
        
        if doctorant:
            interests = doctorant.get("interests", [])
            # Ajouter le domaine s'il n'existe pas déjà
            if domain not in interests:
                interests.append(domain)
                self.chercheurs_collection.update_one(
                    {"_id": doctorant_id},
                    {"$set": {"interests": interests}}
                )
                print(f"Intérêts mis à jour pour {doctorant.get('nom')}")
        
    def recommend_by_domain(self, domain, doctorant_id=None, doctorant_name=None, top_n=10):
        """Génère des recommandations basées sur un domaine spécifique"""
        # Préparation
        if self.publications_df is None:
            self.load_publications()
            self.prepare_publications()
            self.build_model()
            
        # Si l'ID n'est pas fourni mais que le nom l'est, chercher ou créer le doctorant
        if doctorant_id is None and doctorant_name:
            doctorant = self.find_or_create_doctorant(doctorant_name)
            doctorant_id = doctorant["_id"]
            
        # Prétraiter le domaine de recherche
        processed_domain = self.preprocess_text(domain)
        
        # S'assurer que le vectorizer est initialisé
        if self.vectorizer is None:
            print("Le modèle n'est pas initialisé. Initialisation en cours...")
            self.prepare_publications()
            self.build_model()
            
        # Vectoriser le domaine
        try:
            domain_vector = self.vectorizer.transform([processed_domain])
        except Exception as e:
            print(f"Erreur lors de la vectorisation du domaine: {e}")
            # Créer un vecteur vide de même dimension que les vecteurs de publication
            if self.publication_vectors is not None and self.publication_vectors.shape[1] > 0:
                domain_vector = np.zeros((1, self.publication_vectors.shape[1]))
            else:
                print("Impossible de créer un vecteur de domaine compatible.")
                return []
        
        # Calculer la similarité avec toutes les publications
        similarities = cosine_similarity(domain_vector, self.publication_vectors)[0]
        
        # Trouver les indices des publications les plus similaires
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        # Récupérer les publications recommandées
        recommendations = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Ignorer les publications avec score négatif
                pub = self.publications_df.iloc[idx]
                recommendations.append({
                    'publication_id': str(pub.get('_id')),
                    'title': pub.get('title', ''),
                    'abstract': pub.get('abstract_short', ''),
                    'similarity_score': float(similarities[idx]),
                    'keywords': pub.get('keywords', []),
                    'url': pub.get('url', '')
                })
        
        # Si un doctorant est spécifié, mettre à jour son profil
        if doctorant_id:
            # Mettre à jour les intérêts du doctorant
            self.update_doctorant_interests(doctorant_id, domain)
            
            # Enregistrer l'historique de recherche
            search_record = {
                "user_id": doctorant_id,
                "domain": domain,
                "recommendations": recommendations,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            if self.db is None:
                # Mode test: enregistrer l'historique en mémoire
                self.test_search_history.append(search_record)
            else:
                # Mode normal: enregistrer dans MongoDB
                self.search_history_collection.insert_one(search_record)
        
        return recommendations
        
    def get_doctorant_search_history(self, doctorant_id):
        """Récupère l'historique des recherches et recommandations d'un doctorant"""
        if self.db is None:
            # Mode test: filtrer l'historique en mémoire
            return [record for record in self.test_search_history if record["doctorant_id"] == doctorant_id]
            
        # Mode normal: utiliser MongoDB
        history = list(self.search_history_collection.find({"doctorant_id": doctorant_id}))
        return history
    def recommend_by_abstract(self, abstract_text, doctorant_id=None, doctorant_name=None, top_n=10):
        """Génère des recommandations basées sur un résumé de publication fourni"""
        # Préparation
        if self.publications_df is None:
            self.load_publications()
            self.prepare_publications()
            self.build_model()
            
        # Si l'ID n'est pas fourni mais que le nom l'est, chercher ou créer le doctorant
        if doctorant_id is None and doctorant_name:
            doctorant = self.find_or_create_doctorant(doctorant_name)
            doctorant_id = doctorant["_id"]
            
        # Prétraiter le résumé fourni
        processed_abstract = self.preprocess_text(abstract_text)
        
        # S'assurer que le vectorizer est initialisé
        if self.vectorizer is None:
            print("Le modèle n'est pas initialisé. Initialisation en cours...")
            self.prepare_publications()
            self.build_model()
            
        # Vectoriser le résumé
        try:
            abstract_vector = self.vectorizer.transform([processed_abstract])
        except Exception as e:
            print(f"Erreur lors de la vectorisation du résumé: {e}")
            # Créer un vecteur vide de même dimension que les vecteurs de publication
            if self.publication_vectors is not None and self.publication_vectors.shape[1] > 0:
                abstract_vector = np.zeros((1, self.publication_vectors.shape[1]))
            else:
                print("Impossible de créer un vecteur de résumé compatible.")
                return []
        
        # Calculer la similarité avec toutes les publications
        similarities = cosine_similarity(abstract_vector, self.publication_vectors)[0]
        
        # Trouver les indices des publications les plus similaires
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        # Récupérer les publications recommandées
        recommendations = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Ignorer les publications avec score négatif
                pub = self.publications_df.iloc[idx]
                recommendations.append({
                    'publication_id': str(pub.get('_id')),
                    'title': pub.get('title', ''),
                    'abstract': pub.get('abstract_short', ''),
                    'similarity_score': float(similarities[idx]),
                    'keywords': pub.get('keywords', []),
                    'url': pub.get('url', '')
                })
        
        # Si un doctorant est spécifié, enregistrer l'historique de recherche
        if doctorant_id:
            # Extraire quelques mots-clés du résumé pour les stocker comme intérêts
            # On utilise les 5 premiers mots non-stop du résumé comme pseudo-domaine
            if processed_abstract:
                words = processed_abstract.split()
                pseudo_domain = ' '.join(words[:min(5, len(words))])
                
                # Mettre à jour les intérêts du doctorant avec ce pseudo-domaine
                if pseudo_domain:
                    self.update_doctorant_interests(doctorant_id, pseudo_domain)
            
            # Enregistrer l'historique de recherche
            search_record = {
                "user_id": doctorant_id,
                "abstract": abstract_text[:200] + ('...' if len(abstract_text) > 200 else ''),  # Tronquer pour stockage
                "recommendations": recommendations,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            if self.db is None:
                # Mode test: enregistrer l'historique en mémoire
                self.test_search_history.append(search_record)
            else:
                # Mode normal: enregistrer dans MongoDB
                self.search_history_collection.insert_one(search_record)
        
        return recommendations

    def refresh_model(self):
        """Rafraîchit le modèle pour intégrer de nouvelles publications"""
        print("Rafraîchissement du modèle en cours...")
        
        # Sauvegarde temporaire du DataFrame actuel pour comparaison
        old_df_length = 0
        if self.publications_df is not None:
            old_df_length = len(self.publications_df)
        
        # Rechargement des publications
        self.load_publications()
        
        # Vérification si de nouvelles publications ont été ajoutées
        if self.publications_df is not None and len(self.publications_df) > old_df_length:
            print(f"{len(self.publications_df) - old_df_length} nouvelles publications détectées.")
            self.prepare_publications()
            self.build_model()
            print("Modèle rafraîchi avec succès!")
        else:
            print("Aucune nouvelle publication détectée. Le modèle reste inchangé.")    
    def initialize_system(self):
        """Initialise le système de recommandation"""
        self.load_publications()
        self.prepare_publications()
        self.build_model()
        print("Système initialisé et prêt à générer des recommandations!")


def main():
    # Créer l'instance du recommandeur
    recommender = DomainBasedRecommender()
    
    # Initialiser le système
    recommender.initialize_system()
    
    # Exemple: recherche par un doctorant existant ou nouveau
    doctorants_name = ["Doctorant1 ","Doctorant2","Doctorant3 ","Doctorant4","Doctorant5","Doctorant6",]
    domains = ["intelligence artificielle","algorithmes","data engineering","Data science","Data analyst"]
    
    for j in range(6):
        recommendations = recommender.recommend_by_domain(
            domain=domains[j],
            doctorant_name=doctorants_name[j],
            top_n=5
        )
        # Afficher les résultats
        print(f"\nRecommandations Doctorant : '{doctorants_name[j]}' pour '{domains[j]}':")
        for i, rec in enumerate(recommendations):
            print(f"{i+1}. {rec['title']} (Score: {rec['similarity_score']:.4f})")
            print(f"   Keywords: {', '.join(rec['keywords'])}")
            print(f"   URL: {rec['url']}\n")

if __name__ == "__main__":
    main()