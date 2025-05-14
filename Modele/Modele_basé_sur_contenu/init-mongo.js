// Ce script sera exécuté lorsque MongoDB démarre pour initialiser la base de données
db = db.getSiblingDB('Donnees');

// Création des collections si elles n'existent pas
if (!db.getCollectionNames().includes('auteurs')) {
    db.createCollection('auteurs');
    print('Collection "auteurs" créée avec succès');
}

if (!db.getCollectionNames().includes('Publications')) {
    db.createCollection('Publications');
    print('Collection "Publications" créée avec succès');
}

if (!db.getCollectionNames().includes('Statistiques')) {
    db.createCollection('Statistiques');
    print('Collection "Statistiques" créée avec succès');
}

if (!db.getCollectionNames().includes('SearchHistory')) {
    db.createCollection('SearchHistory');
    print('Collection "SearchHistory" créée avec succès');
}