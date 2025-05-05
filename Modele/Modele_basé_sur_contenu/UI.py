from flask import Flask, request, jsonify, render_template
from modele import DomainBasedRecommender
import os
import pickle

app = Flask(__name__)

# Créer le répertoire de cache s'il n'existe pas
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_cache")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")
VECTORS_PATH = os.path.join(MODEL_DIR, "publication_vectors.pkl")
PUBLICATIONS_PATH = os.path.join(MODEL_DIR, "publications_df.pkl")

# Créer le répertoire de cache s'il n'existe pas
print(f"Vérification du répertoire de cache: {MODEL_DIR}")
if not os.path.exists(MODEL_DIR):
    print(f"Création du répertoire de cache: {MODEL_DIR}")
    try:
        os.makedirs(MODEL_DIR)
        print(f"Répertoire de cache créé avec succès")
    except Exception as e:
        print(f"Erreur lors de la création du répertoire de cache: {e}")
else:
    print(f"Le répertoire de cache existe déjà")
force_reload = False
# Initialiser le recommandeur
print("Initialisation du système de recommandation...")
recommender = DomainBasedRecommender()

# Vérifier si le modèle est déjà en cache
if (not force_reload and os.path.exists(VECTORIZER_PATH) and 
    os.path.exists(VECTORS_PATH) and 
    os.path.exists(PUBLICATIONS_PATH)):
    
    print("Chargement du modèle depuis le cache...")
    try:
        # Charger les données du cache
        with open(VECTORIZER_PATH, 'rb') as f:
            recommender.vectorizer = pickle.load(f)
        
        with open(VECTORS_PATH, 'rb') as f:
            recommender.publication_vectors = pickle.load(f)
            
        with open(PUBLICATIONS_PATH, 'rb') as f:
            recommender.publications_df = pickle.load(f)
            
        print("Modèle chargé avec succès depuis le cache!")
    except Exception as e:
        print(f"Erreur lors du chargement du cache: {e}")
        # Si erreur, initialiser normalement
        recommender.load_publications()
        recommender.prepare_publications()
        recommender.build_model()
        
        # Puis sauvegarder le modèle
        with open(VECTORIZER_PATH, 'wb') as f:
            pickle.dump(recommender.vectorizer, f)
            
        with open(VECTORS_PATH, 'wb') as f:
            pickle.dump(recommender.publication_vectors, f)
            
        with open(PUBLICATIONS_PATH, 'wb') as f:
            pickle.dump(recommender.publications_df, f)
else:
    print("Premier démarrage, construction du modèle...")
    # Initialiser le système
    recommender.load_publications()
    recommender.prepare_publications()
    recommender.build_model()
    
    # Sauvegarder le modèle pour les prochains démarrages
    print("Sauvegarde du modèle dans le cache...")
    with open(VECTORIZER_PATH, 'wb') as f:
        pickle.dump(recommender.vectorizer, f)
        
    with open(VECTORS_PATH, 'wb') as f:
        pickle.dump(recommender.publication_vectors, f)
        
    with open(PUBLICATIONS_PATH, 'wb') as f:
        pickle.dump(recommender.publications_df, f)
        
print("Système initialisé avec succès!")

@app.route('/')
def index():
    return render_template('search_form.html')

@app.route('/recommend', methods=['POST'])
def get_recommendations():
    data = request.form
    doctorant_name = data.get('name')
    search_type = data.get('search_type', 'domain')  # Par défaut, recherche par domaine
    
    if not doctorant_name:
        return jsonify({"error": "Le nom du doctorant est requis"}), 400
    
    try:
        if search_type == 'domain':
            domain = data.get('domain')
            if not domain:
                return jsonify({"error": "Le domaine de recherche est requis pour ce type de recherche"}), 400
                
            recommendations = recommender.recommend_by_domain(
                domain=domain,
                doctorant_name=doctorant_name,
                top_n=10
            )
            
            return jsonify({
                'doctorant': doctorant_name,
                'search_type': 'domain',
                'query': domain,
                'recommendations': recommendations
            })
            
        elif search_type == 'abstract':
            abstract = data.get('abstract')
            if not abstract:
                return jsonify({"error": "Le résumé est requis pour ce type de recherche"}), 400
                
            recommendations = recommender.recommend_by_abstract(
                abstract_text=abstract,
                doctorant_name=doctorant_name,
                top_n=10
            )
            
            return jsonify({
                'doctorant': doctorant_name,
                'search_type': 'abstract',
                'query': abstract[:100] + ('...' if len(abstract) > 100 else ''),  # Tronquer pour l'affichage
                'recommendations': recommendations
            })
        else:
            return jsonify({"error": "Type de recherche non reconnu"}), 400
            
    except Exception as e:
        print(f"Erreur lors de la génération des recommandations: {e}")
        return jsonify({"error": f"Une erreur s'est produite: {str(e)}"}), 500

@app.route('/health')
def health_check():
    # Point de terminaison pour vérifier si le serveur est en cours d'exécution
    return jsonify({"status": "ok"})

@app.route('/popular-domains')
def popular_domains():
    # Récupérer les domaines les plus populaires
    domains = recommender.get_popular_domains(limit=5)
    return jsonify(domains)

@app.route('/refresh-model', methods=['POST'])
def refresh_model():
    # Endpoint pour rafraîchir le modèle manuellement si nécessaire
    try:
        recommender.load_publications()
        recommender.prepare_publications()
        recommender.build_model()
        
        # Mettre à jour le cache
        with open(VECTORIZER_PATH, 'wb') as f:
            pickle.dump(recommender.vectorizer, f)
            
        with open(VECTORS_PATH, 'wb') as f:
            pickle.dump(recommender.publication_vectors, f)
            
        with open(PUBLICATIONS_PATH, 'wb') as f:
            pickle.dump(recommender.publications_df, f)
            
        return jsonify({"status": "success", "message": "Modèle rafraîchi avec succès"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erreur: {str(e)}"}), 500

@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    try:
        if os.path.exists(VECTORIZER_PATH):
            os.remove(VECTORIZER_PATH)
        if os.path.exists(VECTORS_PATH):
            os.remove(VECTORS_PATH)
        if os.path.exists(PUBLICATIONS_PATH):
            os.remove(PUBLICATIONS_PATH)
        
        return jsonify({"status": "success", "message": "Cache vidé avec succès"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erreur: {str(e)}"}), 500

# Assurer que le dossier templates existe
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
    print(f"Dossier templates créé: {templates_dir}")

if __name__ == '__main__':
    app.run(debug=True)