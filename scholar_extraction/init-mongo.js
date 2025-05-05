// Initialisation des collections dans MongoDB
db = db.getSiblingDB('Donnees');

// Création des collections si elles n'existent pas
if (!db.getCollectionNames().includes('authors')) {
    db.createCollection('authors');
    print('Collection authors créée');
}

if (!db.getCollectionNames().includes('Publications')) {
    db.createCollection('Publications');
    print('Collection Publications créée');
}

if (!db.getCollectionNames().includes('Statistiques')) {
    db.createCollection('Statistiques');
    print('Collection Statistiques créée');
}

print('Initialisation des collections terminée');