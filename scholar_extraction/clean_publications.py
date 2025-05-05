import pandas as pd
import sys
import os
from datetime import datetime
import logging
from tqdm import tqdm
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_cleaning.log'),
        logging.StreamHandler()  # Ajouter un handler pour la console
    ]
)
logger = logging.getLogger(__name__)

# Importer le MongoConnector pour la gestion de la connexion
from mongo_connector import MongoConnector
from config import COLLECTIONS

def load_publications_to_df(mongo_connector):
    """Charge les publications dans un DataFrame pandas."""
    try:
        print("Chargement des publications...")
        collection = mongo_connector.get_collection(COLLECTIONS["publications"])
        if collection is None:
            logger.error("Impossible d'accéder à la collection des publications")
            print("Impossible d'accéder à la collection des publications")
            return pd.DataFrame()
        
        # Récupérer les données par lots pour éviter une surcharge mémoire
        batch_size = 1000
        publications_data = []
        
        # Compter le nombre total de documents pour la barre de progression
        total_docs = collection.count_documents({})
        logger.info(f"Nombre total de publications à récupérer: {total_docs}")
        print(f"Nombre total de publications à récupérer: {total_docs}")
        
        # Utiliser le skip/limit pour la pagination ou utiliser un cursor avec batch_size
        cursor = collection.find({}).batch_size(batch_size)
        
        # Récupérer les données par lots avec logging de progression
        docs_processed = 0
        for doc in cursor:
            publications_data.append(doc)
            docs_processed += 1
            
            # Log tous les batch_size documents
            if docs_processed % batch_size == 0:
                logger.info(f"Récupéré {docs_processed}/{total_docs} publications ({docs_processed/total_docs*100:.1f}%)")
                print(f"Récupéré {docs_processed}/{total_docs} publications ({docs_processed/total_docs*100:.1f}%)")
        
        # Log final pour le dernier lot (potentiellement incomplet)
        if docs_processed % batch_size != 0:
            logger.info(f"Récupéré {docs_processed}/{total_docs} publications ({docs_processed/total_docs*100:.1f}%)")
            print(f"Récupéré {docs_processed}/{total_docs} publications ({docs_processed/total_docs*100:.1f}%)")
        
        total_pubs = len(publications_data)
        logger.info(f"Chargement terminé: {total_pubs} publications chargées dans le DataFrame")
        print(f"Chargement terminé: {total_pubs} publications chargées dans le DataFrame")
        
        if not publications_data:
            logger.warning("Aucune publication trouvée dans la collection")
            print("Aucune publication trouvée dans la collection")
            return pd.DataFrame()
            
        return pd.DataFrame(publications_data)
    except Exception as e:
        logger.error(f"Erreur lors du chargement des publications: {e}")
        print(f"Erreur lors du chargement des publications: {e}")
        return pd.DataFrame()
    
def clean_dataframe(df):
    """Nettoie le DataFrame des publications."""
    if df.empty:
        return df
    
    logger.info(f"Début du nettoyage du DataFrame ({len(df)} entrées)")
    print(f"Début du nettoyage du DataFrame ({len(df)} entrées)")
    initial_count = len(df)
    
    # Créer une copie du DataFrame original
    df_clean = df.copy()
    
    # 1. Suppression des doublons basés sur hal_id
    if 'hal_id' in df_clean.columns:
        before_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=['hal_id'], keep='first')
        diff = before_count - len(df_clean)
        logger.info(f"Suppression des doublons par hal_id: {diff} entrées supprimées")
        print(f"Suppression des doublons par hal_id: {diff} entrées supprimées")
    
    # 2. Suppression des doublons basés sur titre et année
    if 'title' in df_clean.columns and 'year' in df_clean.columns:
        before_count = len(df_clean)
        # Normalisation des titres (minuscules, suppression des espaces multiples)
        df_clean['title_normalized'] = df_clean['title'].str.lower().str.strip().replace(r'\s+', ' ', regex=True)
        df_clean = df_clean.drop_duplicates(subset=['title_normalized', 'year'], keep='first')
        df_clean = df_clean.drop(columns=['title_normalized'])
        diff = before_count - len(df_clean)
        logger.info(f"Suppression des doublons par titre et année: {diff} entrées supprimées")
        print(f"Suppression des doublons par titre et année: {diff} entrées supprimées")
    
    # 3. Suppression des publications sans titre
    if 'title' in df_clean.columns:
        before_count = len(df_clean)
        df_clean = df_clean[df_clean['title'].notna() & (df_clean['title'] != "")]
        diff = before_count - len(df_clean)
        logger.info(f"Suppression des publications sans titre: {diff} entrées supprimées")
        print(f"Suppression des publications sans titre: {diff} entrées supprimées")
    
    # 4. Normalisation des années
    if 'year' in df_clean.columns:
        # Convertir les années en chaînes de caractères
        df_clean['year'] = df_clean['year'].astype(str)
        # Extraire uniquement les chiffres des années (4 chiffres consécutifs)
        df_clean['year'] = df_clean['year'].str.extract(r'(\d{4})', expand=False)
        # Remplacer les valeurs nulles ou vides par une chaîne vide
        df_clean['year'] = df_clean['year'].fillna("")
        logger.info("Normalisation des années terminée")
        print("Normalisation des années terminée")
    
    # 5. Normalisation des citations (convertir en entier)
    if 'citations' in df_clean.columns:
        df_clean['citations'] = pd.to_numeric(df_clean['citations'], errors='coerce').fillna(0).astype(int)
        logger.info("Normalisation des citations terminée")
        print("Normalisation des citations terminée")
    
    # 6. Vérification et correction des URLs
    if 'url' in df_clean.columns:
        # Remplacer les URLs nulles par des chaînes vides
        df_clean['url'] = df_clean['url'].fillna("")
        # Vérifier si les URLs commencent par http:// ou https://
        mask = (df_clean['url'] != "") & (~df_clean['url'].str.startswith(('http://', 'https://')))
        df_clean.loc[mask, 'url'] = 'https://' + df_clean.loc[mask, 'url']
        logger.info(f"Correction des URLs: {mask.sum()} URLs corrigées")
        print(f"Correction des URLs: {mask.sum()} URLs corrigées")
    
    # 7. Standardisation des auteurs (conversion en liste si ce n'est pas déjà le cas)
    if 'authors' in df_clean.columns:
        def standardize_authors(authors):
            if isinstance(authors, list):
                return authors
            elif isinstance(authors, str):
                try:
                    # Essayer de convertir une chaîne JSON en liste
                    return json.loads(authors)
                except:
                    # Sinon, diviser par des virgules
                    return [author.strip() for author in authors.split(',')]
            else:
                return []
        
        df_clean['authors'] = df_clean['authors'].apply(standardize_authors)
        logger.info("Standardisation des auteurs terminée")
        print("Standardisation des auteurs terminée")
    
    # 8. Vérification de la cohérence des dates
    date_columns = ['date_extraction', 'date_mise_a_jour']
    for col in date_columns:
        if col in df_clean.columns:
            # Standardiser le format des dates
            try:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                # Remplacer les dates invalides par NaT (Not a Time)
                invalid_dates = df_clean[col].isna()
                logger.info(f"Correction des dates dans {col}: {invalid_dates.sum()} dates invalides")
                print(f"Correction des dates dans {col}: {invalid_dates.sum()} dates invalides")
            except Exception as e:
                logger.warning(f"Erreur lors de la standardisation des dates pour {col}: {e}")
                print(f"Erreur lors de la standardisation des dates pour {col}: {e}")
    
    logger.info(f"Nettoyage terminé. {initial_count - len(df_clean)} entrées supprimées au total.")
    print(f"Nettoyage terminé. {initial_count - len(df_clean)} entrées supprimées au total.")
    return df_clean

def update_mongodb(mongo_connector, df_clean):
    """Met à jour la base de données MongoDB avec les données nettoyées sans créer de sauvegarde."""
    try:
        print("Mise à jour directe de la collection des publications...")
        logger.info("Mise à jour directe de la collection des publications...")
        
        # Obtenir une référence à la collection des publications
        collection = mongo_connector.get_collection(COLLECTIONS['publications'])
        
        if collection is None:
            logger.error("Impossible d'accéder à la collection des publications")
            print("Impossible d'accéder à la collection des publications")
            return False
        
        # Vider la collection actuelle
        print("Suppression des données existantes de la collection...")
        logger.info("Suppression des données existantes de la collection...")
        collection.delete_many({})
        logger.info("Données supprimées de la collection originale")
        print("Données supprimées de la collection originale")
        
        # Convertir le DataFrame en dictionnaires et insérer dans la collection
        records = df_clean.to_dict('records')
        
        if records:
            print(f"Insertion de {len(records)} documents dans la collection...")
            logger.info(f"Insertion de {len(records)} documents dans la collection...")
            
            # Insérer par lots pour améliorer les performances
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                collection.insert_many(batch)
                print(f"Lot {i//batch_size + 1}/{(len(records)-1)//batch_size + 1} inséré")
                
            logger.info(f"{len(records)} documents insérés dans la collection")
            print(f"{len(records)} documents insérés dans la collection")
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de MongoDB: {e}")
        print(f"Erreur lors de la mise à jour de MongoDB: {e}")
        return False

def generate_stats(df):
    """Génère des statistiques sur les données nettoyées."""
    print("Génération des statistiques...")
    logger.info("Génération des statistiques...")
    
    stats = {}
    
    if df.empty:
        return stats
    
    stats['total_publications'] = len(df)
    
    if 'year' in df.columns:
        # Statistiques par année
        year_counts = df['year'].value_counts().sort_index()
        stats['publications_by_year'] = year_counts.to_dict()
        stats['oldest_year'] = year_counts.index.min() if not year_counts.empty else "N/A"
        stats['newest_year'] = year_counts.index.max() if not year_counts.empty else "N/A"
    
    if 'citations' in df.columns:
        # Statistiques de citations
        stats['total_citations'] = int(df['citations'].sum())
        stats['avg_citations_per_publication'] = float(df['citations'].mean())
        stats['max_citations'] = int(df['citations'].max())
        
        # Publications les plus citées
        most_cited = df.nlargest(10, 'citations')[['title', 'citations', 'year']]
        stats['most_cited_publications'] = most_cited.to_dict('records')
    
    if 'authors' in df.columns:
        # Statistiques sur les auteurs
        all_authors = []
        for author_list in df['authors']:
            if isinstance(author_list, list):
                all_authors.extend(author_list)
        
        author_counts = pd.Series(all_authors).value_counts()
        stats['total_authors'] = len(author_counts)
        stats['most_published_authors'] = author_counts.head(20).to_dict()
    
    print("Statistiques générées avec succès")
    logger.info("Statistiques générées avec succès")
    return stats

def save_stats_to_mongodb(mongo_connector, stats):
    """Sauvegarde les statistiques dans MongoDB."""
    try:
        if not stats:
            logger.warning("Aucune statistique à sauvegarder")
            print("Aucune statistique à sauvegarder")
            return False
        
        print("Sauvegarde des statistiques dans MongoDB...")
        logger.info("Sauvegarde des statistiques dans MongoDB...")
        
        stats['date_generation'] = datetime.now()
        
        stats_collection = mongo_connector.get_collection(COLLECTIONS['stats'])
        if stats_collection is None:
            logger.error("Impossible d'accéder à la collection des statistiques")
            print("Impossible d'accéder à la collection des statistiques")
            return False
        
        stats_collection.insert_one(stats)
        logger.info("Statistiques sauvegardées dans MongoDB")
        print("Statistiques sauvegardées dans MongoDB")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des statistiques: {e}")
        print(f"Erreur lors de la sauvegarde des statistiques: {e}")
        return False

def main():
    try:
        print("=== DÉBUT DU PROCESSUS DE NETTOYAGE ===")
        logger.info("=== DÉBUT DU PROCESSUS DE NETTOYAGE ===")
        
        # Connexion à la base de données avec MongoConnector
        print("Initialisation de la connexion MongoDB...")
        mongo_connector = MongoConnector()
        connected = mongo_connector.connect()
        
        if not connected:
            logger.error("Impossible de se connecter à MongoDB. Le script s'arrête.")
            print("Impossible de se connecter à MongoDB. Le script s'arrête.")
            return
        
        # Chargement des publications dans un DataFrame
        df = load_publications_to_df(mongo_connector)
        
        if df.empty:
            logger.warning("Aucune donnée à nettoyer")
            print("Aucune donnée à nettoyer")
            return
        
        # Nettoyage du DataFrame
        df_clean = clean_dataframe(df)
        
        # Mise à jour de la base de données
        success = update_mongodb(mongo_connector, df_clean)
        
        if success:
            # Génération et sauvegarde des statistiques
            stats = generate_stats(df_clean)
            save_stats_to_mongodb(mongo_connector, stats)
            
            # Afficher un résumé
            print("=== RÉSUMÉ DU NETTOYAGE ===")
            logger.info("=== RÉSUMÉ DU NETTOYAGE ===")
            print(f"Publications avant nettoyage: {len(df)}")
            logger.info(f"Publications avant nettoyage: {len(df)}")
            print(f"Publications après nettoyage: {len(df_clean)}")
            logger.info(f"Publications après nettoyage: {len(df_clean)}")
            print(f"Entrées supprimées: {len(df) - len(df_clean)}")
            logger.info(f"Entrées supprimées: {len(df) - len(df_clean)}")
            print("=== FIN DU PROCESSUS DE NETTOYAGE ===")
            logger.info("=== FIN DU PROCESSUS DE NETTOYAGE ===")
        else:
            logger.error("Le processus de nettoyage a échoué lors de la mise à jour de la base de données")
            print("Le processus de nettoyage a échoué lors de la mise à jour de la base de données")
        
        # Fermer la connexion MongoDB
        mongo_connector.close()
        
    except Exception as e:
        logger.error(f"Erreur générale: {e}")
        print(f"Erreur générale: {e}")
        logger.error("Le processus de nettoyage a échoué")
        print("Le processus de nettoyage a échoué")

if __name__ == "__main__":
    main()