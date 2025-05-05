from scholarly import scholarly
import time
from config import MAX_AUTHORS_RESULTS, MAX_PUBLICATIONS, SEARCH_DELAY

class GoogleScholarExtractor:
    @staticmethod
    @staticmethod
    def search_author(author_name, affiliation=None):
        """Recherche un auteur sur Google Scholar"""
        print(f"Recherche de {author_name}...")
        try:
            search_query = scholarly.search_author(author_name)
            authors = []
            
            try:
                for i in range(MAX_AUTHORS_RESULTS):
                    author = next(search_query)
                    # Si une affiliation est spécifiée, vérifier la correspondance
                    if affiliation and affiliation.lower() in author.get('affiliation', '').lower():
                        authors.append(author)
                    else:
                        authors.append(author)
                    print(f"Auteur trouvé: {author.get('name', 'Nom inconnu')}")
            except StopIteration:
                print("Fin de l'itération des résultats")
            
            print(f"Nombre d'auteurs trouvés: {len(authors)}")
            return authors
        except Exception as e:
            print(f"Erreur lors de la recherche de l'auteur: {str(e)}")
            return []
    
    @staticmethod
    def get_author_details(author):
        """Récupère les détails complets d'un auteur"""
        try:
            author_details = scholarly.fill(author)
            print("Détails de l'auteur récupérés avec succès.")
            return author_details
        except Exception as e:
            print(f"Erreur lors de la récupération des détails: {e}")
            return author
    
    @staticmethod
    def get_publications(author_details):
        """Récupère les publications d'un auteur"""
        publications = author_details.get('publications', [])
        print(f"Nombre de publications trouvées: {len(publications)}")
        detailed_publications = []
        for i, pub in enumerate(publications):  # Supprimez la limite [:MAX_PUBLICATIONS]
            try:
                print(f"Récupération des détails de la publication {i+1}/{len(publications)}...")
                filled_pub = scholarly.fill(pub)
                detailed_publications.append(filled_pub)
                time.sleep(SEARCH_DELAY)
            except Exception as e:
                print(f"Erreur pour la publication {i+1}: {e}")
                detailed_publications.append(pub)
        
        return detailed_publications
    
    @staticmethod
    def search_keyword(keyword, max_results=30):
        """Recherche des publications par mot-clé sur Google Scholar"""
        print(f"Recherche de publications pour le mot-clé: {keyword}...")
        try:
            search_query = scholarly.search_pubs(keyword)
            publications = []
            
            try:
                for i in range(max_results):
                    publication = next(search_query)
                    publications.append(publication)
                    print(f"Publication trouvée: {publication.get('bib', {}).get('title', 'Titre inconnu')}")
                    time.sleep(SEARCH_DELAY)  # Pause pour éviter de surcharger l'API
            except StopIteration:
                print("Fin de l'itération des résultats")
            
            print(f"Nombre de publications trouvées pour '{keyword}': {len(publications)}")
            return publications
        except Exception as e:
            print(f"Erreur lors de la recherche de publications: {str(e)}")
            return []