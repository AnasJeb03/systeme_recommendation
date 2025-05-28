FROM python:3.9-slim

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV AIRFLOW_HOME=/app/airflow

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Créer les répertoires nécessaires
WORKDIR /app
RUN mkdir -p /app/model_cache /app/logs /app/Modele/Modele_basé_sur_contenu

# Copier les fichiers du projet
COPY automation/ /app/automation/
COPY Modele/ /app/Modele/
COPY config.py /app/config.py

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
    apache-airflow==2.5.3 \
    pandas \
    numpy \
    scikit-learn \
    mlflow==2.3.1 \
    pymongo \
    requests

# Créer les dossiers pour Airflow
RUN mkdir -p ${AIRFLOW_HOME}/dags ${AIRFLOW_HOME}/logs ${AIRFLOW_HOME}/plugins

# Copier les DAGs vers le dossier approprié
RUN cp /app/automation/dags/recommendation_dags.py ${AIRFLOW_HOME}/dags/

# Exposer les ports pour Airflow et MLflow
EXPOSE 8080 5000

# Définir le volume pour persister les données
VOLUME ["/app/model_cache", "/app/airflow/logs"]

# Le répertoire de travail de l'application
WORKDIR /app

# Commande par défaut: exécute directement le script d'automatisation
CMD ["python", "/app/automation/pipeline_automatisation.py"]