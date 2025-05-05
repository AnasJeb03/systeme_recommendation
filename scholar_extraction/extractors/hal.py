"""
Extracteur pour la plateforme HAL (Hyper Articles en Ligne).
Ce module permet d'extraire des données bibliographiques depuis l'API HAL.
"""

import time
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class HALExtractor:
    """
    Classe pour extraire des données bibliographiques depuis HAL.
    HAL est une archive ouverte française qui contient des articles scientifiques.
    """
    
    BASE_URL = "https://api.archives-ouvertes.fr/search"
    
    def __init__(self, max_results: int = 10000):
        """
        Initialise l'extracteur HAL.
        
        Args:
            max_results: Nombre maximum de résultats à récupérer par requête
        """
        self.max_results = max_results
        logger.info("HALExtractor initialisé avec max_results=%d", max_results)
    
    def extract_by_author(self, author_name: str) -> List[Dict[str, Any]]:
        """
        Extrait toutes les publications d'un auteur spécifique depuis HAL avec pagination.
        
        Args:
            author_name: Nom de l'auteur à rechercher
                
        Returns:
            Liste complète des publications de l'auteur
        """
        logger.info(f"Extraction paginée des publications pour l'auteur: {author_name}")
        
        all_publications = []
        start = 0
        rows_per_page = 1000  # Nombre de résultats par page
        total_found = None
        
        while total_found is None or start < total_found:
            params = {
                'q': f'authFullName_s:"{author_name}"',
                'fl': 'docid,title_s,authFullName_s,publicationDate_s,journalTitle_s,description_s,abstract_s,abstractText_s,label_s,'
                'citationFull_s,uri_s,authIdHal_s,authStructId_i,structName_s',
                'rows': rows_per_page,
                'start': start,
                'sort': 'publicationDate_s desc',
                'wt': 'json'
            }
            
            try:
                response = requests.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Mise à jour du total trouvé si pas encore défini
                if total_found is None:
                    total_found = data.get('response', {}).get('numFound', 0)
                    logger.info(f"Total de publications trouvées pour {author_name}: {total_found}")
                
                # Traitement des publications de cette page
                page_publications = []
                for doc in data.get('response', {}).get('docs', []):
                    # Même code de traitement que dans la méthode extract_by_author
                    abstract = ''
                    for field in ['description_s', 'abstract_s', 'abstractText_s', 'label_s']:
                        if field in doc:
                            abstract_data = doc.get(field)
                            if isinstance(abstract_data, list) and abstract_data:
                                abstract = abstract_data[0]
                            elif isinstance(abstract_data, str):
                                abstract = abstract_data
                            if abstract:
                                break
                    
                    publication = {
                        'title': doc.get('title_s', ''),
                        'authors': doc.get('authFullName_s', []),
                        'publication_date': doc.get('publicationDate_s', ''),
                        'journal': doc.get('journalTitle_s', ''),
                        'abstract': abstract,
                        'citation': doc.get('citationFull_s', ''),
                        'url': doc.get('uri_s', ''),
                        'id': doc.get('docid', ''),
                        'source': 'hal',
                        'extracted_date': datetime.now().isoformat()
                    }
                    page_publications.append(publication)
                
                all_publications.extend(page_publications)
                logger.info(f"Page {start//rows_per_page + 1}: {len(page_publications)} publications récupérées")
                
                # Incrémenter pour la prochaine page
                start += rows_per_page
                
                # Petite pause pour ne pas surcharger l'API
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur lors de l'extraction depuis HAL: {str(e)}")
                break
        
        logger.info(f"Extraction paginée terminée: {len(all_publications)} publications totales trouvées pour {author_name}")
        return all_publications
    
    def extract_by_keyword(self, keyword: str,languages=None) -> List[Dict[str, Any]]:
        """
        Extrait les publications correspondant à un mot-clé depuis HAL avec pagination.
        
        Args:
            keyword: Mot-clé à rechercher
            languages: Liste des langues à extraire ['fr', 'en']
                
        Returns:
            Liste des publications correspondant au mot-clé
        """
        logger.info(f"Extraction paginée des publications pour le mot-clé: {keyword}")
        
        # Initialiser les langues si non spécifiées
        if languages is None:
            languages = ['fr', 'en']
        
        # Construire la partie de la requête pour les langues
        language_filter = ""
        if languages:
            language_parts = []
            for lang in languages:
                language_parts.append(f'language_s:"{lang}"')
            if language_parts:
                language_filter = " AND (" + " OR ".join(language_parts) + ")"
        
        all_publications = []
        start = 0
        rows_per_page = 100
        total_found = None
        
        while total_found is None or start < total_found:
            logger.info(f"Récupération de la page {start//rows_per_page + 1} pour '{keyword}'")
            print(f"Récupération de la page {start//rows_per_page + 1} pour '{keyword}'...")
            
            # Inclure le filtre de langue dans la requête
            query = f'(text:"{keyword}" OR title_t:"{keyword}" OR keyword_s:"{keyword}"){language_filter}'
            
            params = {
                'q': query,
                'fl': 'docid,title_s,authFullName_s,publicationDate_s,journalTitle_s,description_s,abstract_s,abstractText_s,label_s,citationFull_s,uri_s,language_s',
                'rows': rows_per_page,
                'start': start,
                'sort': 'publicationDate_s desc',
                'wt': 'json'
            }
            
            try:
                # Ajouter un timeout pour éviter un blocage indéfini
                response = requests.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Mise à jour du total trouvé si pas encore défini
                if total_found is None:
                    total_found = data.get('response', {}).get('numFound', 0)
                    logger.info(f"Total de publications trouvées pour '{keyword}': {total_found}")
                    print(f"Total de publications trouvées pour '{keyword}': {total_found}")
                    
                    # Si aucun résultat, sortir tout de suite
                    if total_found == 0:
                        return []
                
                # Traitement des publications de cette page
                page_publications = []
                total_docs = len(data.get('response', {}).get('docs', []))
                logger.info(f"Traitement de {total_docs} documents dans la page actuelle")
                print(f"Traitement de {total_docs} documents dans la page actuelle")
                
                for i, doc in enumerate(data.get('response', {}).get('docs', [])):
                    # Code de traitement comme dans la méthode originale
                    abstract = ''
                    for field in ['description_s', 'abstract_s', 'abstractText_s', 'label_s']:
                        if field in doc:
                            abstract_data = doc.get(field)
                            if isinstance(abstract_data, list) and abstract_data:
                                abstract = abstract_data[0]
                            elif isinstance(abstract_data, str):
                                abstract = abstract_data
                            if abstract:
                                break
                    
                    title = doc.get('title_s', '')
                    if isinstance(title, list) and title:
                        title = title[0]
                    
                    if (i+1) % 10 == 0:  # Log tous les 10 documents
                        logger.info(f"Publication {i+1}/{total_docs}: {title}")
                        print(f"Publication {i+1}/{total_docs}: {title}")
                    
                    publication = {
                        'title': title,
                        'authors': doc.get('authFullName_s', []),
                        'publication_date': doc.get('publicationDate_s', ''),
                        'journal': doc.get('journalTitle_s', ''),
                        'abstract': abstract,
                        'citation': doc.get('citationFull_s', ''),
                        'url': doc.get('uri_s', ''),
                        'id': doc.get('docid', ''),
                        'source': 'hal',
                        'extracted_date': datetime.now().isoformat()
                    }
                    page_publications.append(publication)
                
                all_publications.extend(page_publications)
                logger.info(f"Page {start//rows_per_page + 1}: {len(page_publications)} publications ajoutées")
                print(f"Page {start//rows_per_page + 1}: {len(page_publications)} publications ajoutées")
                
                # Incrémenter pour la prochaine page
                start += rows_per_page
                
                # Pause pour éviter de surcharger l'API
                time.sleep(1)
                
                # Si on a tout récupéré ou presque, on sort
                if start >= total_found:
                    break
                    
            except requests.exceptions.Timeout:
                logger.error(f"Timeout lors de la requête HAL pour '{keyword}' (page {start//rows_per_page + 1})")
                print(f"Timeout lors de la requête HAL pour '{keyword}' (page {start//rows_per_page + 1})")
                break
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur lors de l'extraction depuis HAL: {str(e)}")
                print(f"Erreur lors de l'extraction depuis HAL: {str(e)}")
                break
        
        logger.info(f"Extraction paginée terminée: {len(all_publications)} publications totales trouvées pour '{keyword}'")
        print(f"Extraction paginée terminée: {len(all_publications)} publications totales trouvées pour '{keyword}'")
        return all_publications