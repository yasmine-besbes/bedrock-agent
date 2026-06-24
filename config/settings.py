import os
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════
# REMPLACE PAR LE MODEL ID QUI A FONCTIONNÉ
# À L'ÉTAPE 3
# ══════════════════════════════════════════════════
MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
# ══════════════════════════════════════════════════

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Paramètres du modèle
MODEL_CONFIG = {
    "temperature": 0.7,
    "max_tokens": 1000,
}
# Paramètres de recherche
SEARCH_CONFIG = {
    "max_results": 5,       # Nombre de résultats à retourner
    "region": "fr-fr",      # Région pour les résultats DuckDuckGo
}

# Clé Tavily (optionnel - laisser vide si tu utilises DuckDuckGo)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
# Base de données
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "entreprise.db"
)
DATABASE_URL = f"sqlite:///{DB_PATH}"

# API Météo (Open-Meteo - gratuit, sans clé API)
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"

# DynamoDB - Mémoire long terme
DYNAMODB_TABLE_NAME = "agent_conversations"

# DynamoDB - Historique des conversations (affichage UI)
CHAT_HISTORY_TABLE_NAME = "agent_chat_history"