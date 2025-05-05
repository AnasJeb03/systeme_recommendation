def load_test_data(self):
        """Charge des données de test pour le développement"""
        print("Chargement des données de test...")
        # Exemple de publications pour les tests
        test_publications = [
            {
                "_id": 1,
                "title": "Introduction à l'intelligence artificielle",
                "abstract_full": "Cet article présente les principes fondamentaux de l'intelligence artificielle et ses applications.",
                "abstract_short": "Présentation des principes fondamentaux de l'IA.",
                "keywords": ["intelligence artificielle", "machine learning", "deep learning"],
                "url": "https://example.com/ai-intro"
            },
            {
                "_id": 2,
                "title": "Applications du deep learning dans la vision par ordinateur",
                "abstract_full": "Cet article explore les applications des réseaux de neurones profonds dans le domaine de la vision par ordinateur.",
                "abstract_short": "Applications des réseaux de neurones en vision par ordinateur.",
                "keywords": ["deep learning", "vision par ordinateur", "CNN"],
                "url": "https://example.com/dl-vision"
            },
            {
                "_id": 3,
                "title": "Traitement du langage naturel avec BERT",
                "abstract_full": "Une analyse détaillée de l'utilisation du modèle BERT pour le traitement du langage naturel et ses performances.",
                "abstract_short": "Analyse de BERT pour le NLP.",
                "keywords": ["NLP", "BERT", "transformer", "language model"],
                "url": "https://example.com/bert-nlp"
            },
            {
                "_id": 4,
                "title": "Systèmes de recommandation basés sur le contenu",
                "abstract_full": "Cet article présente les approches de recommandation basées sur le contenu et leur implémentation.",
                "abstract_short": "Approches de recommandation basées sur le contenu.",
                "keywords": ["systèmes de recommandation", "filtrage basé sur le contenu", "TF-IDF"],
                "url": "https://example.com/content-recommender"
            },
            {
                "_id": 5,
                "title": "Apprentissage par renforcement: concepts et applications",
                "abstract_full": "Une exploration des concepts fondamentaux de l'apprentissage par renforcement et ses applications pratiques.",
                "abstract_short": "Concepts et applications de l'apprentissage par renforcement.",
                "keywords": ["apprentissage par renforcement", "RL", "Markov decision process"],
                "url": "https://example.com/reinforcement-learning"
            },
            {
                "_id": 6,
                "title": "Data mining et analyse de données massives",
                "abstract_full": "Cet article explore les techniques de fouille de données appliquées aux grands ensembles de données.",
                "abstract_short": "Techniques de data mining pour les big data.",
                "keywords": ["data mining", "big data", "analyse de données"],
                "url": "https://example.com/data-mining"
            },
            {
                "_id": 7,
                "title": "Sécurité des systèmes d'information",
                "abstract_full": "Une étude approfondie des méthodes de sécurisation des systèmes d'information face aux cybermenaces.",
                "abstract_short": "Méthodes de sécurisation des SI.",
                "keywords": ["sécurité informatique", "cybersécurité", "cryptographie"],
                "url": "https://example.com/infosec"
            },
            {
                "_id": 8,
                "title": "Réseaux de neurones convolutifs pour la classification d'images",
                "abstract_full": "Cette recherche présente une analyse comparative des architectures CNN pour la classification d'images.",
                "abstract_short": "Analyse des CNN pour la classification d'images.",
                "keywords": ["CNN", "classification d'images", "deep learning", "vision par ordinateur"],
                "url": "https://example.com/cnn-image"
            },
            {
                "_id": 9,
                "title": "Modèles de langage génératifs: GPT et au-delà",
                "abstract_full": "Étude des avancées récentes dans les modèles de langage génératifs et leurs applications.",
                "abstract_short": "Avancées dans les modèles de langage génératifs.",
                "keywords": ["NLP", "modèles génératifs", "GPT", "transformer"],
                "url": "https://example.com/gpt-beyond"
            },
            {
                "_id": 10,
                "title": "Interfaces cerveau-machine: principes et applications",
                "abstract_full": "Cette recherche explore les technologies d'interface cerveau-machine et leurs applications potentielles.",
                "abstract_short": "Technologies d'interface cerveau-machine.",
                "keywords": ["interface cerveau-machine", "BCI", "neurotechnologie"],
                "url": "https://example.com/brain-interface"
            }
        ]
        
        self.publications_df = pd.DataFrame(test_publications)
        print(f"Données de test chargées: {len(self.publications_df)} publications")