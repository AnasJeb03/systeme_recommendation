"""
Extracteur pour la plateforme Semantic Scholar.
Ce module permet d'extraire des données bibliographiques depuis l'API Semantic Scholar.
"""

import time
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import random
logger = logging.getLogger(__name__)

class SemanticScholarExtractor:
    """
    Classe pour extraire des données bibliographiques depuis Semantic Scholar.
    Semantic Scholar est un moteur de recherche gratuit pour la littérature académique.
    """
    
    # URL de base pour l'API Semantic Scholar
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key=None, max_results: int = 100, request_timeout: int = 30):
        """
        Initialise l'extracteur Semantic Scholar.
        
        Args:
            api_key: Clé API pour Semantic Scholar (optionnelle mais recommandée pour éviter les limitations)
            max_results: Nombre maximum de résultats à récupérer par requête
            request_timeout: Délai d'attente maximum pour les requêtes en secondes
        """
        self.max_results = max_results
        self.request_timeout = request_timeout
        self.api_key = api_key
        self.headers = {}
        
        if api_key:
            self.headers["x-api-key"] = api_key
            
        logger.info("SemanticScholarExtractor initialisé avec max_results=%d", max_results)
    
    def extract_by_author(self, author_name: str) -> List[Dict[str, Any]]:
        """
        Extrait toutes les publications d'un auteur spécifique depuis Semantic Scholar.
        
        Args:
            author_name: Nom de l'auteur à rechercher
                
        Returns:
            Liste complète des publications de l'auteur
        """
        logger.info(f"Recherche de l'auteur: {author_name}")
        print(f"Recherche de l'auteur: {author_name} sur Semantic Scholar...")
        
        # 1. Recherche de l'auteur
        author_id = self._search_author(author_name)
        
        if not author_id:
            logger.warning(f"Aucun auteur trouvé pour '{author_name}'")
            print(f"Aucun auteur trouvé pour '{author_name}' sur Semantic Scholar")
            return []
        
        # 2. Récupération des publications de l'auteur
        logger.info(f"Extraction des publications pour l'auteur ID: {author_id}")
        print(f"Extraction des publications pour l'auteur ID: {author_id}")
        
        return self._get_author_papers(author_id)
    
    def _search_author(self, author_name: str) -> Optional[str]:
        """
        Recherche un auteur et renvoie son ID.
        
        Args:
            author_name: Nom de l'auteur à rechercher
        
        Returns:
            ID de l'auteur s'il est trouvé, None sinon
        """
        try:
            # Endpoint de recherche d'auteur
            endpoint = f"{self.BASE_URL}/author/search"
            
            params = {
                "query": author_name,
                "limit": 5  # Limiter à 5 résultats pour la recherche d'auteur
            }
            
            response = requests.get(endpoint, params=params, headers=self.headers, timeout=self.request_timeout)
            response.raise_for_status()
            
            data = response.json()
            authors = data.get("data", [])
            
            if not authors:
                return None
            
            # Sélectionner le premier auteur correspondant
            author = authors[0]
            author_id = author.get("authorId")
            
            logger.info(f"Auteur trouvé: {author.get('name')} (ID: {author_id})")
            print(f"Auteur trouvé: {author.get('name')} (ID: {author_id})")
            
            return author_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la recherche de l'auteur: {str(e)}")
            print(f"Erreur lors de la recherche de l'auteur: {str(e)}")
            return None
    
    def _get_author_papers(self, author_id: str) -> List[Dict[str, Any]]:
        """
        Récupère toutes les publications d'un auteur par son ID.
        
        Args:
            author_id: ID de l'auteur
        
        Returns:
            Liste des publications de l'auteur
        """
        all_papers = []
        offset = 0
        limit = min(100, self.max_results)  # L'API accepte maximum 100 par page
        
        try:
            while True:
                # Endpoint pour les publications d'un auteur
                endpoint = f"{self.BASE_URL}/author/{author_id}/papers"
                
                params = {
                    "offset": offset,
                    "limit": limit,
                    "fields": "title,abstract,venue,year,authors,citations,url,externalIds"
                }
                
                response = requests.get(endpoint, params=params, headers=self.headers, timeout=self.request_timeout)
                response.raise_for_status()
                
                data = response.json()
                papers = data.get("data", [])
                
                if not papers:
                    break
                
                # Transformer les données dans le format standard
                for paper in papers:
                    processed_paper = self._process_paper(paper)
                    all_papers.append(processed_paper)
                
                logger.info(f"Récupéré {len(papers)} publications (offset: {offset})")
                print(f"Récupéré {len(papers)} publications (offset: {offset})")
                
                # Si on a moins de résultats que la limite, c'est qu'on a tout récupéré
                if len(papers) < limit:
                    break
                
                offset += limit
                time.sleep(1)  # Pause pour éviter de surcharger l'API
                
                # Si on a atteint le maximum de résultats souhaité
                if len(all_papers) >= self.max_results:
                    break
            
            return all_papers
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des publications: {str(e)}")
            print(f"Erreur lors de la récupération des publications: {str(e)}")
            return all_papers  # Retourner ce qu'on a déjà récupéré
    
    def extract_by_keyword(self, keyword: str, languages=None) -> List[Dict[str, Any]]:
        """
        Extrait les publications correspondant à un mot-clé depuis Semantic Scholar,
        avec gestion des erreurs et mécanisme de nouvelle tentative.
        
        Args:
            keyword: Mot-clé à rechercher
            languages: Liste des langues à extraire ['fr', 'en'] (filtrage côté client)
                
        Returns:
            Liste des publications correspondant au mot-clé
        """
        logger.info(f"Extraction des publications pour le mot-clé: {keyword}")
        print(f"Extraction des publications pour le mot-clé: {keyword} sur Semantic Scholar...")
        
        all_papers = []
        offset = 0
        limit = min(50, self.max_results)  # Réduit à 50 pour diminuer la charge
        max_retries = 5
        retry_delay = 3  # Délai initial de 3 secondes
        
        try:
            while True:
                # Mécanisme de nouvelle tentative avec backoff exponentiel
                current_retry = 0
                while current_retry < max_retries:
                    try:
                        # Endpoint de recherche de publications
                        endpoint = f"{self.BASE_URL}/paper/search"
                        
                        params = {
                            "query": keyword,
                            "offset": offset,
                            "limit": limit,
                            "fields": "title,abstract,venue,year,authors,url,externalIds"
                            # Remarquez que j'ai retiré "citations" qui peut alourdir la requête
                        }
                        
                        response = requests.get(
                            endpoint, 
                            params=params, 
                            headers=self.headers, 
                            timeout=self.request_timeout
                        )
                        
                        # Si on a une erreur 429, on attend plus longtemps
                        if response.status_code == 429:
                            wait_time = retry_delay * (2 ** current_retry)
                            print(f"Limite de taux atteinte. Attente de {wait_time} secondes avant nouvelle tentative...")
                            time.sleep(wait_time)
                            current_retry += 1
                            continue
                        
                        # Si on a un timeout, on réessaie également
                        if response.status_code == 504:
                            wait_time = retry_delay * (2 ** current_retry)
                            print(f"Timeout du serveur. Attente de {wait_time} secondes avant nouvelle tentative...")
                            time.sleep(wait_time)
                            current_retry += 1
                            continue
                        
                        response.raise_for_status()
                        break  # Sortir de la boucle si la requête a réussi
                        
                    except requests.exceptions.RequestException as e:
                        if current_retry < max_retries - 1:
                            wait_time = retry_delay * (2 ** current_retry)
                            print(f"Erreur lors de la requête: {str(e)}. Nouvelle tentative dans {wait_time} secondes...")
                            time.sleep(wait_time)
                            current_retry += 1
                        else:
                            logger.error(f"Échec après {max_retries} tentatives: {str(e)}")
                            print(f"Échec après {max_retries} tentatives: {str(e)}")
                            return all_papers  # Retourner ce qu'on a déjà récupéré
                
                # Si on est sorti de la boucle sans avoir fait de requête réussie
                if current_retry >= max_retries:
                    return all_papers
                    
                data = response.json()
                papers = data.get("data", [])
                total = data.get("total", 0)
                
                if not papers:
                    break
                
                # Transformer et filtrer les publications
                for paper in papers:
                    processed_paper = self._process_paper(paper)
                    
                    # Filtrer par langue si spécifié
                    if languages and not self._filter_by_language(processed_paper, languages):
                        continue
                        
                    all_papers.append(processed_paper)
                
                logger.info(f"Récupéré {len(papers)} publications (offset: {offset}/{total})")
                print(f"Récupéré {len(papers)} publications (offset: {offset}/{total})")
                
                # Si on a moins de résultats que la limite ou atteint le total, c'est qu'on a tout récupéré
                if len(papers) < limit or offset + limit >= total:
                    break
                
                offset += limit
                
                # Pause plus longue entre les requêtes (ajustable selon les besoins)
                sleep_time = 2 + random.uniform(1, 3)  # Entre 3 et 5 secondes
                print(f"Pause de {sleep_time:.1f} secondes pour respecter les limites de l'API...")
                time.sleep(sleep_time)
                
                # Si on a atteint le maximum de résultats souhaité
                if len(all_papers) >= self.max_results:
                    break
            
            logger.info(f"Total des publications trouvées pour '{keyword}': {len(all_papers)}")
            print(f"Total des publications trouvées pour '{keyword}': {len(all_papers)}")
            return all_papers
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la recherche par mot-clé: {str(e)}")
            print(f"Erreur inattendue lors de la recherche par mot-clé: {str(e)}")
            return all_papers  # Retourner ce qu'on a déjà récupéré
    
    def _process_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforme une publication Semantic Scholar au format standard.
        
        Args:
            paper: Publication au format Semantic Scholar
        
        Returns:
            Publication au format standard
        """
        # Extraire les auteurs
        authors = []
        for author in paper.get("authors", []):
            authors.append(author.get("name", ""))
        
        # Extraire les citations
        citations_count = 0
        if "citations" in paper:
            citations_count = len(paper["citations"])
        
        # Extraire les identifiants externes
        external_ids = paper.get("externalIds", {})
        doi = external_ids.get("DOI", "")
        
        return {
            'title': paper.get("title", ""),
            'authors': authors,
            'publication_date': str(paper.get("year", "")),
            'year': paper.get("year", ""),
            'journal': paper.get("venue", ""),
            'abstract': paper.get("abstract", ""),
            'citation': "",  # Semantic Scholar ne fournit pas de citation formatée
            'url': paper.get("url", ""),
            'id': paper.get("paperId", ""),
            'doi': doi,
            'citations': citations_count,
            'source': 'semantic_scholar',
            'extracted_date': datetime.now().isoformat()
        }
    
    def _filter_by_language(self, paper: Dict[str, Any], languages: List[str]) -> bool:
        """
        Filtre une publication selon la langue.
        
        Args:
            paper: Publication à filtrer
            languages: Liste des langues à conserver
        
        Returns:
            True si la publication est dans une des langues spécifiées, False sinon
        """
        if not languages:
            return True
        
        try:
            from langdetect import detect, LangDetectException
            
            # Combiner le titre et l'abstract pour la détection
            text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
            
            # Si le texte est trop court, on le garde par défaut
            if len(text) < 20:
                return True
            
            # Détecter la langue
            language = detect(text)
            
            # Vérifier si la langue est dans la liste des langues souhaitées
            return language in languages
            
        except (LangDetectException, ImportError):
            # En cas d'erreur ou si langdetect n'est pas disponible, on garde la publication
            return True