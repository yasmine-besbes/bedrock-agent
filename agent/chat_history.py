import boto3
import json
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import CHAT_HISTORY_TABLE_NAME, AWS_REGION


class ChatHistoryManager:
    """Gère la persistance des conversations pour l'affichage (type ChatGPT)."""

    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        self.table = self.dynamodb.Table(CHAT_HISTORY_TABLE_NAME)

    def sauvegarder_message(self, session_id: str, role: str, content: str, etapes_outils=None):
        """Sauvegarde un message dans l'historique d'affichage."""
        timestamp = datetime.now(timezone.utc).isoformat()

        item = {
            "session_id": session_id,
            "timestamp": timestamp,
            "role": role,
            "content": content,
            "etapes_outils": json.dumps(etapes_outils or []),
        }
        self.table.put_item(Item=item)

    def recuperer_messages(self, session_id: str) -> list:
        """Récupère tous les messages d'une session, triés du plus ancien au plus récent."""
        response = self.table.query(
            KeyConditionExpression="session_id = :sid",
            ExpressionAttributeValues={":sid": session_id},
            ScanIndexForward=True  # Plus ancien -> plus récent
        )

        messages = []
        for item in response.get("Items", []):
            messages.append({
                "role": item["role"],
                "content": item["content"],
                "etapes_outils": json.loads(item.get("etapes_outils", "[]"))
            })
        return messages

    def lister_sessions(self) -> list:
        """
        Liste toutes les sessions existantes avec leur titre
        (premier message utilisateur) et la date du dernier message.
        Utilise un Scan car on n'a pas d'index secondaire — suffisant pour un PoC.
        """
        response = self.table.scan()
        items = response.get("Items", [])

        sessions = {}
        for item in items:
            sid = item["session_id"]
            if sid not in sessions:
                sessions[sid] = {
                    "session_id": sid,
                    "premier_message": None,
                    "derniere_date": item["timestamp"]
                }

            if item["role"] == "user" and sessions[sid]["premier_message"] is None:
                sessions[sid]["premier_message"] = item["content"]

            if item["timestamp"] > sessions[sid]["derniere_date"]:
                sessions[sid]["derniere_date"] = item["timestamp"]

        # Trie les sessions par date décroissante (plus récente en premier)
        liste = sorted(sessions.values(), key=lambda x: x["derniere_date"], reverse=True)
        return liste

    def supprimer_session(self, session_id: str):
        """Supprime tous les messages d'une session."""
        response = self.table.query(
            KeyConditionExpression="session_id = :sid",
            ExpressionAttributeValues={":sid": session_id}
        )

        for item in response.get("Items", []):
            self.table.delete_item(
                Key={"session_id": item["session_id"], "timestamp": item["timestamp"]}
            )