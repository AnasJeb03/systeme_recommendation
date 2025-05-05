import sys
print("Script démarré")

try:
    from mongo_connector import MongoConnector
    print("Import de MongoConnector réussi")
    
    connector = MongoConnector()
    print("Instance de MongoConnector créée")
    
    result = connector.connect()
    print(f"Résultat de la connexion: {result}")
    
    if result:
        print("Connexion réussie")
        # Tester l'accès à une collection
        collection = connector.get_collection("Chercheurs/Doctorants")
        if collection:
            count = collection.count_documents({})
            print(f"Nombre de documents dans la collection: {count}")
    else:
        print("Échec de la connexion")
        
except Exception as e:
    print(f"ERREUR: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("Script terminé")