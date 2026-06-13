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