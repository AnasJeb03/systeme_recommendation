# Image de base Python
FROM python:3.9-slim

# Installation des dépendances système minimales
RUN apt-get update && apt-get install -y \
    curl \
    iputils-ping \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .

# Exposer le port de l'application
EXPOSE 8000

# Commande par défaut à exécuter
CMD ["python", "main.py"]