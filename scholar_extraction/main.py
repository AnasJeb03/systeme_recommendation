from extractors.google_scholar import GoogleScholarExtractor
from extractors.hal import HALExtractor
from processors.cleaner import DataCleaner
from processors.stats_generator import StatsGenerator
from database.repository import ScholarRepository
from extractors.semantic_scholar import SemanticScholarExtractor
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time
import re

def process_researcher(name, affiliation=None, sources=None):
    """
    Traite un chercheur complet depuis plusieurs sources: extraction, stockage, nettoyage et statistiques
    
    Args:
        name: Nom du chercheur
        affiliation: Affiliation du chercheur (optionnel)
        sources: Liste des sources à utiliser ['google_scholar', 'hal'] (par défaut les deux)
    """
    # Initialiser les sources d'extraction
    if sources is None:
        sources = ['google_scholar', 'hal', 'semantic_scholar']
    
    # Initialiser le repository
    repo = ScholarRepository()
    
    try:
        # Initialiser les variables pour le chercheur et ses publications
        chercheur_id = None
        all_publications = []
        
        # ===== EXTRACTION DEPUIS GOOGLE SCHOLAR =====
        if 'google_scholar' in sources:
            print("=== Extraction depuis Google Scholar ===")
            chercheur_id = extract_from_google_scholar(name, affiliation, repo)
            if chercheur_id:
                # Récupérer les publications déjà stockées pour les mettre à jour plus tard
                scholar_publications = repo.get_researcher_publications(chercheur_id)
                all_publications.extend(scholar_publications)
                print(f"Nombre de publications trouvées sur Google Scholar: {len(scholar_publications)}")
        
        # ===== EXTRACTION DEPUIS HAL =====
        if 'hal' in sources:
            print("=== Extraction depuis HAL ===")
            # Utiliser le même chercheur_id si déjà créé par Google Scholar
            if not chercheur_id:
                # Si pas encore de chercheur, on crée une entrée basique à partir de HAL
                chercheur_id = extract_researcher_from_hal(name, repo)
            
            # Extraire les publications de HAL
            hal_publications = extract_publications_from_hal(name, chercheur_id, repo)
            all_publications.extend(hal_publications)
            print(f"Nombre de publications trouvées sur HAL: {len(hal_publications)}")
        # ===== EXTRACTION DEPUIS SEMANTIC SCHOLAR =====
        if 'semantic_scholar' in sources:
            print("=== Extraction depuis Semantic Scholar ===")
            if not chercheur_id:
                chercheur_id = extract_researcher_from_semantic_scholar(name, repo)
            
            semantic_publications = extract_publications_from_semantic_scholar(name, chercheur_id, repo)
            all_publications.extend(semantic_publications)
            print(f"Nombre de publications trouvées sur Semantic Scholar: {len(semantic_publications)}")
        
        # Si aucune publication n'a été trouvée, on s'arrête là
        if not all_publications:
            print(f"Aucune publication trouvée pour {name}")
            return
            
        # ===== GÉNÉRATION DES STATISTIQUES =====
        # Récupérer toutes les publications du chercheur de la base de données
        all_db_publications = repo.get_researcher_publications(chercheur_id)
        print(f"Nombre total de publications dans la base de données: {len(all_db_publications)}")
        
        # Générer les statistiques
        stats_doc = StatsGenerator.generate_researcher_stats(all_db_publications, chercheur_id)
        
        # Stocker les statistiques
        stats_id = repo.save_statistics(stats_doc)
        print(f"Statistiques générées avec ID: {stats_id}")
        
    finally:
        # Fermer la connexion à la base de données
        repo.close()
def process_publications_by_keywords(keywords_list, sources=None,languages=None):
    """
    Extrait et traite les publications liées à une liste de mots-clés
    
    Args:
        keywords_list: Liste des mots-clés à rechercher
        sources: Liste des sources à utiliser ['google_scholar', 'hal'] (par défaut les deux)
        languages: Liste des langues à extraire ['fr', 'en'] (par défaut les deux)
    """
    # Initialiser les sources d'extraction
    if sources is None:
        sources = ['google_scholar', 'hal', 'semantic_scholar']
    
    # Initialiser les langues
    if languages is None:
        languages = ['fr', 'en']
    
    # Initialiser le repository
    repo = ScholarRepository()
    
    try:
        for keyword in keywords_list:
            print(f"\n=== Traitement des publications pour le mot-clé: {keyword} ===")
            
            # ===== EXTRACTION DEPUIS GOOGLE SCHOLAR =====
            if 'google_scholar' in sources:
                print(f"Extraction depuis Google Scholar pour le mot-clé: {keyword}")
                extract_publications_by_keyword_from_google_scholar(keyword, repo, languages)
            
            # ===== EXTRACTION DEPUIS HAL =====
            if 'hal' in sources:
                print(f"Extraction depuis HAL pour le mot-clé: {keyword}")
                extract_publications_by_keyword_from_hal(keyword, repo, languages)
            if 'semantic_scholar' in sources:
                print(f"Extraction depuis Semantic Scholar pour le mot-clé: {keyword}")
                extract_publications_by_keyword_from_semantic_scholar(keyword, repo, languages)

            print(f"Traitement terminé pour le mot-clé: {keyword}")
            time.sleep(2)  # Pause entre les mots-clés pour éviter de surcharger les APIs
    
    finally:
        # Fermer la connexion à la base de données
        repo.close()

def extract_researcher_from_semantic_scholar(name, repo):
    """Créé une entrée pour le chercheur basée sur les données Semantic Scholar ou récupère l'ID existant"""
    # Vérifier si le chercheur existe déjà
    existing_researcher = repo.find_researcher_by_name(name)
    
    if existing_researcher:
        chercheur_id = existing_researcher["_id"]
        print(f"Chercheur existant trouvé avec ID: {chercheur_id}")
        
        # Ajouter Semantic Scholar aux sources si pas déjà présent
        if "semantic_scholar" not in existing_researcher.get("sources", []):
            update_doc = {
                "sources": existing_researcher.get("sources", []) + ["semantic_scholar"]
            }
            repo.update_researcher(chercheur_id, update_doc)
            print("Source Semantic Scholar ajoutée au chercheur existant")
        
        return chercheur_id
    else:
        # Extraire des données sur le chercheur depuis Semantic Scholar
        semantic_extractor = SemanticScholarExtractor()
        publications = semantic_extractor.extract_by_author(name)
        
        # Initialiser les informations du chercheur
        affiliation = ""
        interests = []
        citations_total = 0
        
        # Essayer d'extraire l'affiliation et les intérêts à partir des publications
        if publications:
            # Extraire les mots-clés/intérêts à partir des abstracts
            combined_text = " ".join([pub.get('abstract', '') for pub in publications])
            interests = DataCleaner.extract_technical_keywords(combined_text, max_keywords=10)
            
            # Calculer le nombre total de citations
            citations_total = sum(pub.get('citations', 0) for pub in publications)
        
        # Créer un nouveau chercheur
        chercheur_doc = {
            "nom": name,
            "affiliation": affiliation,
            "h_index": 0,  # Semantic Scholar ne fournit pas directement cette information
            "i10_index": 0,  # Semantic Scholar ne fournit pas cette information
            "citations_total": citations_total,
            "interests": interests,
            "scholar_id": "",
            "url_profile": "",
            "sources": ["semantic_scholar"],
            "date_creation": pd.Timestamp.now().isoformat()
        }
        
        # Stocker le chercheur et récupérer son ID
        chercheur_id = repo.save_researcher(chercheur_doc)
        print(f"Chercheur ajouté depuis Semantic Scholar avec ID: {chercheur_id}")
    
    return chercheur_id
def extract_publications_from_semantic_scholar(name, chercheur_id, repo):
    """Extrait les publications depuis Semantic Scholar pour un chercheur donné"""
    # Initialiser l'extracteur Semantic Scholar
    semantic_extractor = SemanticScholarExtractor()
    
    # Extraire les publications
    semantic_publications = semantic_extractor.extract_by_author(name)
    
    # Préparer les documents pour MongoDB
    publications_docs = []
    for pub in semantic_publications:
        title = pub.get('title', '')
        pub_year = pub.get('year', '')
        
        # Vérifier si la publication existe déjà
        existing_pub = repo.find_similar_publication(chercheur_id, title, pub_year)
        if existing_pub:
            print(f"Publication déjà existante dans Semantic Scholar: {title}")
            continue
        
        # Si la publication n'existe pas encore
        full_abstract = pub.get('abstract', '')
        short_summary = DataCleaner.generate_short_summary(full_abstract, max_length=250)
        text = f"{title} {full_abstract}"
        keywords = DataCleaner.extract_keywords(text)
        
        pub_doc = {
            "title": title,
            "abstract_full": full_abstract,
            "abstract_short": short_summary,
            "authors": pub.get('authors', []),
            "year": pub_year,
            "venue": pub.get('journal', ''),
            "citations": pub.get('citations', 0),
            "url": pub.get('url', ''),
            "semantic_scholar_id": pub.get('id', ''),
            "doi": pub.get('doi', ''),
            "chercheur_id": chercheur_id,
            "keywords": keywords,
            "source": "semantic_scholar",
            "date_extraction": pd.Timestamp.now().isoformat()
        }
        publications_docs.append(pub_doc)
    
    # Stocker les publications
    if publications_docs:
        pub_ids = repo.save_publications(publications_docs)
        print(f"{len(pub_ids)} publications ajoutées à MongoDB depuis Semantic Scholar")
        
        # Enrichir les publications avec des mots-clés techniques
        for i, pub_id in enumerate(pub_ids):
            # Nettoyer le titre
            title = DataCleaner.clean_title(publications_docs[i]["title"])
            
            # Extraction plus approfondie des mots-clés
            text = f"{publications_docs[i]['title']} {publications_docs[i]['abstract_full']}"
            enhanced_keywords = DataCleaner.extract_technical_keywords(text)
            
            # Mettre à jour la publication
            repo.update_publication(pub_id, {
                "title": title,
                "keywords": enhanced_keywords
            })
    
    return publications_docs
def extract_publications_by_keyword_from_semantic_scholar(keyword, repo, languages=None, batch_size=100):
    """Extrait les publications depuis Semantic Scholar pour un mot-clé donné"""
    # Initialiser l'extracteur Semantic Scholar
    semantic_extractor = SemanticScholarExtractor()
    
    # Extraire les publications
    semantic_publications = semantic_extractor.extract_by_keyword(keyword, languages)
    total_publications = len(semantic_publications)
    print(f"Début du traitement et de l'insertion de {total_publications} publications dans MongoDB...")
    
    # Traiter les publications par lots
    publications_docs_all = []
    pub_ids_all = []
    
    for i in range(0, total_publications, batch_size):
        batch = semantic_publications[i:i+batch_size]
        print(f"Traitement du lot {i//batch_size + 1}/{(total_publications-1)//batch_size + 1} ({len(batch)} publications)")
        
        # Préparer les documents pour MongoDB
        publications_docs = []
        for pub in batch:
            title = pub.get('title', '')
            pub_year = pub.get('year', '')
            
            # Vérifier si la publication existe déjà
            existing_pub = repo.find_similar_publication_by_title(title, pub_year)
            if existing_pub:
                continue
            
            full_abstract = pub.get('abstract', '')
            short_summary = DataCleaner.generate_short_summary(full_abstract, max_length=250)
            text = f"{title} {full_abstract}"
            keywords = DataCleaner.extract_keywords(text)
            
            pub_doc = {
                "title": title,
                "abstract_full": full_abstract,
                "abstract_short": short_summary,
                "authors": pub.get('authors', []),
                "year": pub_year,
                "venue": pub.get('journal', ''),
                "citations": pub.get('citations', 0),
                "url": pub.get('url', ''),
                "semantic_scholar_id": pub.get('id', ''),
                "doi": pub.get('doi', ''),
                "keywords": keywords,
                "search_keyword": keyword,
                "source": "semantic_scholar",
                "date_extraction": pd.Timestamp.now().isoformat()
            }
            publications_docs.append(pub_doc)
        
        # Stocker le lot de publications
        if publications_docs:
            try:
                pub_ids = repo.save_publications(publications_docs)
                print(f"Lot {i//batch_size + 1}: {len(pub_ids)} publications ajoutées à MongoDB")
                pub_ids_all.extend(pub_ids)
                publications_docs_all.extend(publications_docs)
                
                # Enrichir les publications avec des mots-clés techniques
                for j, pub_id in enumerate(pub_ids):
                    if j % 50 == 0:
                        print(f"Enrichissement des publications: {j}/{len(pub_ids)}")
                    
                    title = DataCleaner.clean_title(publications_docs[j]["title"])
                    text = f"{publications_docs[j]['title']} {publications_docs[j]['abstract_full']}"
                    enhanced_keywords = DataCleaner.extract_technical_keywords(text)
                    
                    repo.update_publication(pub_id, {
                        "title": title,
                        "keywords": enhanced_keywords
                    })
            except Exception as e:
                print(f"Erreur lors du traitement du lot {i//batch_size + 1}: {str(e)}")
    
    print(f"Traitement terminé. {len(pub_ids_all)} publications ajoutées sur {total_publications} extraites.")
    return publications_docs_all
def extract_publications_by_keyword_from_google_scholar(keyword, repo, languages=None):
    """Extrait les publications depuis Google Scholar pour un mot-clé donné"""
    # Rechercher les publications par mot-clé
    publications = GoogleScholarExtractor.search_keyword(keyword)
    
    # Filtrer les publications par langue si spécifié
    if languages:
        from langdetect import detect, LangDetectException
        import re
        filtered_publications = []
        for pub in publications:
            try:
                # Combiner le titre et l'abstract pour la détection
                title = pub.get('title', '')
                if isinstance(title, list) and title:
                    title = title[0]
                abstract = pub.get('bib', {}).get('abstract', '')
                text = f"{title} {abstract}"
                
                # Nettoyer le texte pour une meilleure détection
                clean_text = re.sub(r'[^\w\s]', ' ', text)
                
                # Détecter la langue
                language = detect(clean_text)
                
                # Garder seulement les langues spécifiées
                if language in languages:
                    filtered_publications.append(pub)
                    print(f"Publication conservée (langue: {language}): {title}")
                else:
                    print(f"Publication ignorée (langue: {language}): {title}")
            except LangDetectException:
                # En cas d'erreur, conserver la publication par défaut
                filtered_publications.append(pub)
                print(f"Impossible de détecter la langue, publication conservée: {title}")
        publications = filtered_publications
    
    # Préparer les documents pour MongoDB
    publications_docs = []
    for pub in publications:
        title = pub.get('title', '')
        if isinstance(title, list) and title:
            title = title[0]
        
        # Extraire l'année
        year = pub.get('bib', {}).get('pub_year', '')
        
        # Vérifier si la publication existe déjà (sans chercheur_id)
        existing_pub = repo.find_similar_publication_by_title(title, year)
        if existing_pub:
            print(f"Publication déjà existante: {title}")
            # Mettre à jour les informations (nombre de citations)
            repo.update_publication(existing_pub["_id"], {
                "citations": pub.get('num_citations', 0),
                "date_mise_a_jour": pd.Timestamp.now().isoformat()
            })
            continue
        
        # Traiter une nouvelle publication
        full_abstract = pub.get('bib', {}).get('abstract', '')
        short_summary = DataCleaner.generate_short_summary(full_abstract, max_length=250)
        text = f"{title} {full_abstract}"
        keywords = DataCleaner.extract_keywords(text)
        
        # Liste des auteurs
        authors = pub.get('bib', {}).get('author', [])
        
        pub_doc = {
            "title": title,
            "abstract_full": full_abstract,
            "abstract_short": short_summary,
            "authors": authors,
            "year": year,
            "venue": pub.get('bib', {}).get('venue', ''),
            "citations": pub.get('num_citations', 0),
            "url": pub.get('pub_url', ''),
            "scholar_pub_id": pub.get('pub_id', ''),
            "keywords": keywords,
            "search_keyword": keyword,  # Mot-clé utilisé pour la recherche
            "source": "google_scholar",
            "date_extraction": pd.Timestamp.now().isoformat()
        }
        publications_docs.append(pub_doc)
    
    # Stocker les publications
    if publications_docs:
        pub_ids = repo.save_publications(publications_docs)
        print(f"{len(pub_ids)} publications ajoutées à MongoDB depuis Google Scholar pour le mot-clé: {keyword}")
        
        # Enrichir les publications avec des mots-clés techniques
        for i, pub_id in enumerate(pub_ids):
            # Nettoyer le titre
            title = DataCleaner.clean_title(publications_docs[i]["title"])
            
            # Extraction plus approfondie des mots-clés
            text = f"{publications_docs[i]['title']} {publications_docs[i]['abstract_full']}"
            enhanced_keywords = DataCleaner.extract_technical_keywords(text)
            
            # Mettre à jour la publication
            repo.update_publication(pub_id, {
                "title": title,
                "keywords": enhanced_keywords
            })
    
    return publications_docs

def extract_publications_by_keyword_from_hal(keyword, repo,languages=None, batch_size=500):
    """Extrait les publications depuis HAL pour un mot-clé donné avec traitement par lots"""
    # Initialiser l'extracteur HAL
    hal_extractor = HALExtractor()
    
    # Extraire les publications
    hal_publications = hal_extractor.extract_by_keyword(keyword, languages)
    total_publications = len(hal_publications)
    print(f"Début du traitement et de l'insertion de {total_publications} publications dans MongoDB...")
    
    # Traiter les publications par lots
    publications_docs_all = []
    pub_ids_all = []
    
    for i in range(0, total_publications, batch_size):
        batch = hal_publications[i:i+batch_size]
        print(f"Traitement du lot {i//batch_size + 1}/{(total_publications-1)//batch_size + 1} ({len(batch)} publications)")
        
        # Préparer les documents pour MongoDB (comme dans votre code original)
        publications_docs = []
        for pub in batch:
            # [Votre code de traitement de publication existant]
            title = pub.get('title', '')
            pub_year = ""
            if pub.get('publication_date'):
                try:
                    pub_year = pub.get('publication_date')[:4]
                except:
                    pass
            
            existing_pub = repo.find_similar_publication_by_title(title, pub_year)
            if existing_pub:
                continue
            
            full_abstract = pub.get('abstract', '')
            short_summary = DataCleaner.generate_short_summary(full_abstract, max_length=250)
            text = f"{title} {full_abstract}"
            keywords = DataCleaner.extract_keywords(text)
            
            pub_doc = {
                "title": title,
                "abstract_full": full_abstract,
                "abstract_short": short_summary,
                "authors": pub.get('authors', []),
                "year": pub_year,
                "venue": pub.get('journal', ''),
                "citations": 0,
                "url": pub.get('url', ''),
                "hal_id": pub.get('id', ''),
                "keywords": keywords,
                "search_keyword": keyword,
                "source": "hal",
                "date_extraction": pd.Timestamp.now().isoformat()
            }
            publications_docs.append(pub_doc)
        
        # Stocker le lot de publications
        if publications_docs:
            try:
                pub_ids = repo.save_publications(publications_docs)
                print(f"Lot {i//batch_size + 1}: {len(pub_ids)} publications ajoutées à MongoDB")
                pub_ids_all.extend(pub_ids)
                publications_docs_all.extend(publications_docs)
                
                # Enrichir les publications avec des mots-clés techniques (par petits lots)
                for j, pub_id in enumerate(pub_ids):
                    if j % 50 == 0:
                        print(f"Enrichissement des publications: {j}/{len(pub_ids)}")
                    
                    title = DataCleaner.clean_title(publications_docs[j]["title"])
                    text = f"{publications_docs[j]['title']} {publications_docs[j]['abstract_full']}"
                    enhanced_keywords = DataCleaner.extract_technical_keywords(text)
                    
                    repo.update_publication(pub_id, {
                        "title": title,
                        "keywords": enhanced_keywords
                    })
            except Exception as e:
                print(f"Erreur lors du traitement du lot {i//batch_size + 1}: {str(e)}")
    
    print(f"Traitement terminé. {len(pub_ids_all)} publications ajoutées sur {total_publications} extraites.")
    return publications_docs_all
def extract_from_google_scholar(name, affiliation, repo):
    """Extraction des données depuis Google Scholar"""
    # 1. Rechercher l'auteur
    authors = GoogleScholarExtractor.search_author(name, affiliation)
    
    if not authors:
        print(f"Aucun auteur trouvé sur Google Scholar pour {name}")
        return None
    
    # Sélectionner le premier auteur
    selected_author = authors[0]
    print(f"Auteur sélectionné: {selected_author['name']} ({selected_author.get('affiliation', 'Affiliation inconnue')})")
    
    # 2. Récupérer les détails de l'auteur
    author_details = GoogleScholarExtractor.get_author_details(selected_author)
    
    # 3. Vérifier si le chercheur existe déjà dans la base de données
    existing_researcher = repo.find_researcher_by_name(author_details.get('name', name))
    
    chercheur_id = None
    
    if existing_researcher:
        chercheur_id = existing_researcher["_id"]
        print(f"Chercheur existant trouvé avec ID: {chercheur_id}")
        
        # Mettre à jour les informations du chercheur
        update_doc = {
            "h_index": author_details.get('hindex', 0),
            "i10_index": author_details.get('i10index', 0),
            "citations_total": author_details.get('citedby', 0),
            "interests": author_details.get('interests', []),
        }
        
        # Ajouter Google Scholar aux sources si pas déjà présent
        if "google_scholar" not in existing_researcher.get("sources", []):
            update_doc["sources"] = existing_researcher.get("sources", []) + ["google_scholar"]
        
        repo.update_researcher(chercheur_id, update_doc)
        print(f"Chercheur mis à jour avec les nouvelles informations de Google Scholar")
    else:
        # 4. Créer le document du chercheur s'il n'existe pas
        chercheur_doc = {
            "nom": author_details.get('name', name),
            "affiliation": author_details.get('affiliation', ''),
            "h_index": author_details.get('hindex', 0),
            "i10_index": author_details.get('i10index', 0),
            "citations_total": author_details.get('citedby', 0),
            "interests": author_details.get('interests', []),
            "scholar_id": author_details.get('scholar_id', ''),
            "url_profile": author_details.get('url_picture', ''),
            "sources": ["google_scholar"]
        }
        
        # Stocker le chercheur et récupérer son ID
        chercheur_id = repo.save_researcher(chercheur_doc)
        print(f"Nouveau chercheur ajouté avec ID: {chercheur_id}")
    
    # 5. Récupérer les publications
    publications = GoogleScholarExtractor.get_publications(author_details)
    
    # 6. Préparer les documents de publications
    publications_docs = []
    for pub in publications:
        # Obtenir le titre propre
        title = pub.get('title', '')
        if isinstance(title, list) and title:
            title = title[0]
        
        # Obtenir l'année
        year = pub.get('bib', {}).get('pub_year', '')
        
        # Vérifier si la publication existe déjà
        existing_pub = repo.find_similar_publication(chercheur_id, title, year)
        if existing_pub:
            print(f"Publication déjà existante: {title}")
            # Optionnel: mettre à jour les informations (par exemple le nombre de citations)
            repo.update_publication(existing_pub["_id"], {
                "citations": pub.get('num_citations', 0),
                "date_mise_a_jour": pd.Timestamp.now().isoformat()
            })
            continue  # Passer à la publication suivante
        
        # Si on arrive ici, c'est que la publication n'existe pas encore
        # Le reste du code reste inchangé
        full_abstract = pub.get('bib', {}).get('abstract', '')
        short_summary = DataCleaner.generate_short_summary(full_abstract, max_length=250)
        text = f"{title} {full_abstract}"
        keywords = DataCleaner.extract_keywords(text)
        
        pub_doc = {
            "title": title,
            "abstract_full": full_abstract,
            "abstract_short": short_summary,
            "authors": pub.get('bib', {}).get('author', []),
            "year": year,
            "venue": pub.get('bib', {}).get('venue', ''),
            "citations": pub.get('num_citations', 0),
            "url": pub.get('pub_url', ''),
            "scholar_pub_id": pub.get('pub_id', ''),
            "chercheur_id": chercheur_id,
            "keywords": keywords,
            "source": "google_scholar",
            "date_extraction": pd.Timestamp.now().isoformat()
        }
        publications_docs.append(pub_doc)
    # 7. Stocker les publications
    if publications_docs:
        pub_ids = repo.save_publications(publications_docs)
        print(f"{len(pub_ids)} publications ajoutées à MongoDB depuis Google Scholar")
        
        # 8. Affiner le nettoyage et enrichir les publications
        for i, pub_id in enumerate(pub_ids):
            # Nettoyer le titre
            title = DataCleaner.clean_title(publications_docs[i]["title"])
            
            # Extraction plus approfondie des mots-clés avec des termes composés
            text = f"{publications_docs[i]['title']} {publications_docs[i]['abstract_full']}"
            enhanced_keywords = DataCleaner.extract_technical_keywords(text)
            
            # Mettre à jour la publication avec les mots-clés améliorés
            repo.update_publication(pub_id, {
                "title": title,
                "keywords": enhanced_keywords
            })
    
    return chercheur_id

def extract_researcher_from_hal(name, repo):
    """Créé une entrée plus complète pour le chercheur basée sur les données HAL ou récupère l'ID existant"""
    # Vérifier si le chercheur existe déjà
    existing_researcher = repo.find_researcher_by_name(name)
    
    if existing_researcher:
        chercheur_id = existing_researcher["_id"]
        print(f"Chercheur existant trouvé avec ID: {chercheur_id}")
        
        # Ajouter HAL aux sources si pas déjà présent
        if "hal" not in existing_researcher.get("sources", []):
            update_doc = {
                "sources": existing_researcher.get("sources", []) + ["hal"]
            }
            repo.update_researcher(chercheur_id, update_doc)
            print("Source HAL ajoutée au chercheur existant")
        
        return chercheur_id
    else:
        # Extraire des données supplémentaires sur le chercheur depuis HAL
        hal_extractor = HALExtractor()
        # Recherche des publications pour obtenir des informations sur l'auteur
        publications = hal_extractor.extract_by_author(name)
        
        # Initialiser les informations du chercheur
        affiliation = ""
        interests = []
        
        # Essayer d'extraire l'affiliation et les intérêts à partir des publications
        if publications:
            # Extraire les mots-clés/intérêts à partir des abstracts des publications
            combined_text = " ".join([pub.get('abstract', '') for pub in publications])
            interests = DataCleaner.extract_technical_keywords(combined_text, max_keywords=10)
            
            # Essayer de trouver une affiliation dans les publications
            for pub in publications:
                if 'citation' in pub and pub['citation']:
                    citation = pub['citation']
                    # Rechercher des parties qui pourraient contenir une affiliation
                    # Exemple: "Author Name (University Name, Department)"
                    affiliation_match = re.search(r'\((.*?)\)', citation)
                    if affiliation_match:
                        affiliation = affiliation_match.group(1)
                        break
        
        # Créer un nouveau chercheur avec les informations disponibles
        chercheur_doc = {
            "nom": name,
            "affiliation": affiliation,
            "h_index": 0,  # HAL ne fournit pas cette information
            "i10_index": 0,  # HAL ne fournit pas cette information
            "citations_total": 0,  # On pourrait essayer de calculer à partir des publications
            "interests": interests,
            "scholar_id": "",  # HAL ne fournit pas d'ID Google Scholar
            "url_profile": "",  # On pourrait ajouter un lien vers le profil HAL si disponible
            "sources": ["hal"],
            "date_creation": pd.Timestamp.now().isoformat()
        }
        
        # Calculer le nombre total de citations si disponible
        # Note: HAL ne fournit généralement pas cette information
        
        # Stocker le chercheur et récupérer son ID
        chercheur_id = repo.save_researcher(chercheur_doc)
        print(f"Chercheur ajouté depuis HAL avec ID: {chercheur_id}")
    return chercheur_id

def extract_publications_from_hal(name, chercheur_id, repo):
    """Extrait les publications depuis HAL pour un chercheur donné"""
    # Initialiser l'extracteur HAL
    hal_extractor = HALExtractor()
    
    # Extraire les publications
    hal_publications = hal_extractor.extract_by_author(name)
    
    # Préparer les documents pour MongoDB
    publications_docs = []
    for pub in hal_publications:
        title = pub.get('title', '')
        
        # Convertir la date de publication en année
        pub_year = ""
        if pub.get('publication_date'):
            try:
                pub_year = pub.get('publication_date')[:4]  # Prendre les 4 premiers caractères (YYYY)
            except:
                pass
        
        # Vérifier si la publication existe déjà
        existing_pub = repo.find_similar_publication(chercheur_id, title, pub_year)
        if existing_pub:
            print(f"Publication déjà existante dans HAL: {title}")
            continue  # Passer à la publication suivante
        
        # Si on arrive ici, c'est que la publication n'existe pas encore
        # Le reste du code reste inchangé
        full_abstract = pub.get('abstract', '')
        short_summary = DataCleaner.generate_short_summary(full_abstract, max_length=250)
        text = f"{title} {full_abstract}"
        keywords = DataCleaner.extract_keywords(text)
        
        pub_doc = {
            "title": title,
            "abstract_full": full_abstract,
            "abstract_short": short_summary,
            "authors": pub.get('authors', []),
            "year": pub_year,
            "venue": pub.get('journal', ''),
            "citations": 0,  # HAL ne fournit pas cette information
            "url": pub.get('url', ''),
            "hal_id": pub.get('id', ''),
            "chercheur_id": chercheur_id,
            "keywords": keywords,
            "source": "hal",
            "date_extraction": pd.Timestamp.now().isoformat()
        }
        publications_docs.append(pub_doc)
    
    # Stocker les publications
    if publications_docs:
        pub_ids = repo.save_publications(publications_docs)
        print(f"{len(pub_ids)} publications ajoutées à MongoDB depuis HAL")
        
        # Enrichir les publications avec des mots-clés techniques
        for i, pub_id in enumerate(pub_ids):
            # Nettoyer le titre
            title = DataCleaner.clean_title(publications_docs[i]["title"])
            
            # Extraction plus approfondie des mots-clés
            text = f"{publications_docs[i]['title']} {publications_docs[i]['abstract_full']}"
            enhanced_keywords = DataCleaner.extract_technical_keywords(text)
            
            # Mettre à jour la publication
            repo.update_publication(pub_id, {
                "title": title,
                "keywords": enhanced_keywords
            })
    
    return publications_docs

def process_multiple_researchers(researcher_names, affiliation=None, sources=None):
    """
    Traite plusieurs chercheurs en parallèle
    
    Args:
        researcher_names: Liste des noms de chercheurs
        affiliation: Affiliation optionnelle (s'applique à tous)
        sources: Sources d'extraction à utiliser
    """
    print(f"Traitement de {len(researcher_names)} chercheurs...")
    
    for i, name in enumerate(researcher_names):
        print(f"\n--- Chercheur {i+1}/{len(researcher_names)}: {name} ---")
        process_researcher(name, affiliation, sources)
        # Pause entre les chercheurs pour éviter de surcharger les APIs
        if i < len(researcher_names) - 1:
            time.sleep(5)
    
    print("Traitement terminé pour tous les chercheurs.")

if __name__ == "__main__":
    # process_researcher("Labib Yousef", sources=["hal"])
    
    # Exemple avec sources spécifiques
    #process_researcher("Labib Yousef", sources=["google_scholar"])
    #process_researcher("Mhand Hifi", sources=["google_scholar","hal"])
    
    """
    chercheurs = [
    "Barrandon Ludovic",
    "Benhabib Karim",
    "Cochard Gérard-Michel",
    "Chkir Mouna",
    "Coorevits Patrice",
    "Dahmani Isma",
    "Hernandez Marisela",
    "Hifi Mhand",
    "Lazure Dominique",
    "Marie Christophe",
    "Negre Stéphane",
    "Montrelay Nicolas",
    "Nguyen Vietdung",
    "Pierens Xavier",
    "Saadi Toufik",
    "Saint Fabien",
    "Tassin Regis",
    "T'Kint Michèle",
    "Wu Lei",
    "Youssef Labib",
    "ABDI DAHER Oumalkaire",
    "DOUMBOUYA Naby",
    "Boulebene Sabrine",
    "Brahimi Sihem",
    "Dey Imène",
    "Latram Khadidja",
    "Samod Elmi Samod",
    "Belhadj Narjes",
    "Gacem Oussama",
    "Baatout Fatma Zohra",
    "Boukhari Samah",
    "Ferroum Meriem",
    "Youssouf Amir Mohamed",
    "Sadeghsa Shohre",
    "NGUYEN Thi Le Quyen",
    "Thekra Al-Douri",
    "Moudher Al-Hameed",
    "Najat Al-Hameed",
    "Al-Mohamadawi Ali",
    "Ferhan Al-Maliky",
    "Mohamad Ali",
    "Sherko Arkawazi",
    "Belhadj Belkacem",
    "Hiba Bederina",
    "Ahmed Bellil",
    "Adel Bouchekhchoukha",
    "Isma Dahmani",
    "Nawal Haddadou",
    "Tayeb Hocine",
    "Habib Kadari",
    "Rézika Kheffache",
    "Asma Mansri",
    "Laurent Moreau",
    "Ibrahim Moussa",
    "Orwa Omran",
    "Sagvan Saleh",
    "Labib Yousef",
    "Ines Zarrad",
    "Ahmed Ziregue"
    ]
    
    """
    keywords = [
    # Apprentissage automatique avancé
    "deep learning architecture optimization", "transformer neural networks", "contrastive learning frameworks",
    "bayesian neural networks", "probabilistic graphical models", "variational inference methods",
    "reinforcement learning algorithms", "deep Q-networks", "policy gradient methods", "actor-critic algorithms",
    "multi-agent reinforcement learning", "game theory optimization", "nash equilibrium in ML",
    
    # IA théorique et mathématique
    "computational learning theory", "PAC learning", "statistical learning bounds",
    "information theoretic learning", "Kolmogorov complexity", "minimum description length",
    "kernel methods", "reproducing kernel Hilbert spaces", "support vector theory",
    "optimization algorithms", "stochastic gradient descent convergence", "second-order optimization methods",
    "non-convex optimization", "saddle point problems", "manifold optimization techniques",
    
    # Traitement automatique des langues
    "neural machine translation models", "cross-lingual representation learning", "multilingual transformers",
    "language model pretraining techniques", "contextualized word embeddings", "token classification tasks",
    "discourse analysis algorithms", "coreference resolution models", "syntactic parsing methods",
    "sequence-to-sequence architectures", "attention mechanism variants", "transformer decoder analysis",
    
    # Vision par ordinateur
    "convolutional neural network architectures", "object detection algorithms", "Faster R-CNN variants",
    "semantic segmentation methods", "instance segmentation techniques", "panoptic segmentation frameworks",
    "visual reasoning models", "scene graph generation", "visual question answering architectures",
    "3D reconstruction algorithms", "structure from motion techniques", "neural radiance fields",
    
    # Systèmes de recommandation et graphes
    "graph convolutional networks", "graph attention networks", "graph representation learning",
    "knowledge graph embedding models", "entity alignment techniques", "ontology reasoning algorithms",
    "collaborative filtering algorithms", "matrix factorization techniques", "factorization machines",
    "session-based recommendation models", "sequential recommendation algorithms", "user preference modeling",
    
    # Apprentissage automatique spécialisé
    "meta-learning algorithms", "few-shot classification methods", "prototypical networks",
    "self-supervised representation learning", "contrastive predictive coding", "bootstrap your own latent",
    "transfer learning techniques", "domain adaptation methods", "adversarial domain adaptation",
    "continual learning approaches", "catastrophic forgetting mitigation", "elastic weight consolidation",
    
    # Modèles génératifs
    "variational autoencoders", "normalizing flows", "autoregressive models",
    "generative adversarial network architectures", "StyleGAN innovations", "adversarial training stability",
    "diffusion probabilistic models", "score-based generative models", "denoising diffusion techniques",
    "energy-based models", "Langevin dynamics", "MCMC sampling methods for generative models",
    
    # Séries temporelles et anomalies
    "recurrent neural network variants", "gated recurrent architectures", "temporal convolutional networks",
    "state space models for time series", "Kalman filtering techniques", "hidden Markov models",
    "multivariate time series forecasting", "temporal point processes", "neural ODE methods",
    "density-based anomaly detection", "reconstruction-based anomaly detection", "deep SVDD methods",
    
    # MLOps et systèmes ML
    "hyperparameter optimization techniques", "neural architecture search algorithms", "differentiable architecture search",
    "ML system design patterns", "distributed training algorithms", "parameter server architectures",
    "model quantization methods", "knowledge distillation techniques", "neural network pruning algorithms",
    "hardware-aware neural networks", "ML compiler optimization", "accelerator-specific neural networks",
    
    # Éthique, explicabilité et robustesse
    "algorithmic fairness metrics", "bias mitigation techniques", "fairness-aware learning algorithms",
    "interpretable machine learning methods", "explainable AI frameworks", "feature attribution techniques",
    "adversarial robustness methods", "certified robustness", "randomized smoothing techniques",
    "privacy-preserving machine learning", "federated learning algorithms", "secure multi-party computation for ML",
    
    # Applications scientifiques et spécialisées
    "computational biology deep learning", "protein structure prediction algorithms", "genomic sequence analysis",
    "scientific machine learning", "physics-informed neural networks", "differential equation solvers",
    "quantum machine learning algorithms", "quantum neural network architectures", "variational quantum algorithms",
    "robotics reinforcement learning", "sim-to-real transfer methods", "imitation learning algorithms"
]
    process_publications_by_keywords(keywords,sources=["hal","google scholar"], languages=["en", "fr"])
    #process_multiple_researchers(chercheurs,sources=["google_scholar","hal"])
