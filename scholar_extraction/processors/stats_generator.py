import pandas as pd

class StatsGenerator:
    @staticmethod
    def generate_researcher_stats(publications, researcher_id):
        """Génère des statistiques pour un chercheur à partir de ses publications"""
        stats = {
            "total_publications": len(publications),
            "total_citations": sum(pub.get('citations', 0) for pub in publications),
            "average_citations": sum(pub.get('citations', 0) for pub in publications) / len(publications) if publications else 0,
            "publications_par_annee": {},
            "publication_la_plus_citee": "",
            "citations_max": 0
        }
        
        # Publications par année - convertir les années en chaînes de caractères
        for pub in publications:
            year = pub.get('year')
            if year:
                year_str = str(year)  # Convertir en chaîne de caractères
                stats["publications_par_annee"][year_str] = stats["publications_par_annee"].get(year_str, 0) + 1
        
        # Publication la plus citée
        for pub in publications:
            citations = pub.get('citations', 0)
            if citations > stats["citations_max"]:
                stats["citations_max"] = citations
                stats["publication_la_plus_citee"] = pub.get('title', '')
        
        # Créer le document de statistiques
        stats_doc = {
            "chercheur_id": researcher_id,
            "date_generation": pd.Timestamp.now().isoformat(),
            "stats": stats
        }
        
        return stats_doc