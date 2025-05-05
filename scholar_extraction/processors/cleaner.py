import re
from collections import Counter
import nltk
from nltk.tokenize import sent_tokenize

class DataCleaner:
   # Liste des mots vides en français et anglais (comme avant)
    STOPWORDS = ["le", "la", "les", "de", "du", "des", "un", "une", "et", "est", 
                "en", "que", "qui", "dans", "pour", "sur", "avec", "par",
                "the", "a", "an", "of", "to", "in", "is", "and", "that", "for",
                "are", "was", "were", "be", "been", "by", "at", "this", "from", "as",
                "we", "our", "their", "these", "those", "his", "her", "its", "they",
                "has", "have", "had", "will", "would", "could", "should"]
    
    # Liste des termes techniques (comme avant)
    TECH_TERMS = {
        # Intelligence Artificielle
        "intelligence artificielle": ["ai", "artificial intelligence", "intelligence artificielle"],
        "machine learning": ["ml", "machine learning", "apprentissage automatique", "apprentissage machine"],
        "deep learning": ["deep learning", "réseaux neuronaux", "neural networks", "réseau de neurones"],
        "traitement du langage naturel": ["nlp", "natural language processing", "traitement du langage", "analyse de texte"],

        # Informatique
        "programmation": ["programmation", "coding", "developer", "développeur", "code", "software"],
        "bases de données": ["database", "sql", "nosql", "mongodb", "mysql", "postgresql"],
        "cybersécurité": ["cybersecurity", "sécurité informatique", "vulnérabilité", "attaque", "protection", "hacking"],
        "systèmes distribués": ["distributed systems", "système distribué", "cloud", "microservices"],
        "internet des objets": ["iot", "internet of things", "objets connectés"],

        # Science des données
        "data science": ["data science", "science des données", "analyse de données", "data analysis"],
        "big data": ["big data", "grandes données", "hadoop", "spark"],
        "visualisation de données": ["data visualization", "visualisation", "graphique", "dashboard"],

        # Recherche scientifique
        "recherche scientifique": ["scientific research", "publication", "revue scientifique", "journal"],
        "bibliométrie": ["bibliométrie", "citation", "index h", "impact factor"],

        # Mathématiques / Statistiques
        "statistiques": ["statistics", "statistique", "régression", "moyenne", "écart-type"],
        "algorithmes": ["algorithme", "algorithm", "tri", "recherche", "optimisation"],

        # Autres domaines connexes
        "robotique": ["robot", "robotique", "autonomous systems"],
        "vision par ordinateur": ["computer vision", "vision par ordinateur", "détection d’objets", "segmentation"],
        "data engineering": ["data engineering", "ingénierie des données", "ETL", "data pipeline", "data warehouse"],
        "data mining": ["data mining", "fouille de données", "exploration de données", "text mining"],
        "data analysis": ["data analysis", "analyse de données", "pandas", "numpy", "dataframe"],
        "artificial neural networks": ["neural network", "réseau neuronal", "ANN", "CNN", "RNN", "LSTM", "GRU"],
        "reinforcement learning": ["reinforcement learning", "apprentissage par renforcement", "RL", "Q-learning"],
        "natural language processing": ["NLP", "natural language processing", "traitement du langage naturel", "sentiment analysis"],
        "computer vision": ["computer vision", "vision par ordinateur", "image recognition", "object detection"],
        "data visualization": ["data visualization", "visualisation de données", "tableau", "d3.js", "plotly"],
        "business intelligence": ["business intelligence", "BI", "intelligence d'affaires", "decision support"],
        "predictive analytics": ["predictive analytics", "analyse prédictive", "forecasting", "prévision"],
        "explainable AI": ["explainable AI", "XAI", "interprétabilité", "explicabilité"],
        "federated learning": ["federated learning", "apprentissage fédéré", "decentralized learning"],
        "transfer learning": ["transfer learning", "apprentissage par transfert", "fine-tuning"],
        "genetic algorithms": ["genetic algorithms", "algorithmes génétiques", "evolutionary computation"],
        "quantum computing": ["quantum computing", "informatique quantique", "quantum machine learning"],
        "edge computing": ["edge computing", "informatique en périphérie", "IoT analytics"],
    }

    
    @staticmethod
    def clean_title(title):
        """Nettoie un titre"""
        if not title:
            return title
        
        # Si le titre est une liste, prendre le premier élément
        if isinstance(title, list):
            if not title:  # Liste vide
                return ""
            title = title[0]  # Prendre le premier élément
        
        return title.strip()
    
    @staticmethod
    def extract_keywords(text, max_keywords=10):
        """Extrait des mots-clés simples d'un texte"""
        # Même code qu'avant
        if not text:
            return []
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        filtered_words = [w for w in words if w not in DataCleaner.STOPWORDS]
        word_counts = Counter(filtered_words)
        keywords = [word for word, count in word_counts.most_common(max_keywords)]
        
        return keywords
    
    @staticmethod
    def extract_technical_keywords(text, max_keywords=15):
        """Extrait des mots-clés techniques, incluant les termes composés"""
        # Même code qu'avant
        if not text:
            return []
        
        text_lower = text.lower()
        found_terms = []
        
        for category, terms in DataCleaner.TECH_TERMS.items():
            for term in terms:
                if term in text_lower:
                    found_terms.append(category)
                    break
        
        simple_keywords = DataCleaner.extract_keywords(text, max_keywords=max_keywords - len(found_terms))
        combined_keywords = found_terms + [k for k in simple_keywords if k not in found_terms]
        
        return combined_keywords[:max_keywords]
    
    @staticmethod
    def generate_short_summary(abstract, max_length=250):
        """
        Génère un petit résumé à partir d'un abstract complet.
        Le résumé extrait les premières phrases jusqu'à atteindre max_length caractères.
        """
        if not abstract:
            return ""
        
        # Vérifier si le package punkt est déjà téléchargé
        try:
            # Essayer de tokenizer en phrases directement
            sentences = sent_tokenize(abstract)
        except LookupError:
            # Si le package n'est pas disponible, le télécharger une seule fois
            nltk.download('punkt', quiet=True)
            try:
                sentences = sent_tokenize(abstract)
            except:
                # Fallback: découper par points
                sentences = [s.strip() + '.' for s in abstract.split('.') if s.strip()]
        
        # Si l'abstract est déjà court, le retourner tel quel
        if len(abstract) <= max_length:
            return abstract
        
        # Construire le résumé phrase par phrase jusqu'à la longueur maximale
        summary = ""
        for sentence in sentences:
            if len(summary + sentence) <= max_length:
                summary += sentence + " "
            else:
                break
        
        # Nettoyer et ajouter une indication que c'est un résumé
        summary = summary.strip()
        if summary and len(summary) < len(abstract):
            summary += "..."
            
        return summary