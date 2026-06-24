FROM python:3.12-slim

WORKDIR /app

# Installe les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copie et installe les dépendances Python en premier (optimise le cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le reste du code de l'application
COPY . .

# Génère la base de données SQLite si elle n'existe pas déjà
RUN python data/create_database.py

# Crée le dossier logs si nécessaire
RUN mkdir -p logs

EXPOSE 8501

# Vérifie que l'app répond correctement
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true"]