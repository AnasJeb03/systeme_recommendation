FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier les fichiers du projet
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p model_cache templates

# Exposer le port utilisé par l'application
EXPOSE 8000

# Définir les variables d'environnement
ENV PYTHONUNBUFFERED=1

# Définir la commande par défaut mais sans entrypoint pour permettre de la surcharger facilement
CMD ["python", "UI.py"]