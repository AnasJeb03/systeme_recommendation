// Script d'initialisation MongoDB
db = db.getSiblingDB('Donnees');

// Création des collections
db.createCollection('publications');
db.createCollection('auteurs');
db.createCollection('recommendations');

// Création d'un utilisateur avec des droits appropriés
// Seulement si on n'est pas en mode d'authentification dans MongoDB
try {
  db.createUser({
    user: 'app_user',
    pwd: 'password',
    roles: [
      { role: 'readWrite', db: 'Donnees' }
    ]
  });
  print("Utilisateur app_user créé avec succès");
} catch (error) {
  print("Note: Impossible de créer l'utilisateur - " + error.message);
}

// Création d'index pour améliorer les performances
db.publications.createIndex({ "title": "text" });
db.publications.createIndex({ "authors": 1 });
db.auteurs.createIndex({ "name": 1 }, { unique: true });

print("Initialisation de MongoDB terminée avec succès");