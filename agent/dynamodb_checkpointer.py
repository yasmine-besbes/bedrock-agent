import boto3
import json
import pickle
import base64
from datetime import datetime, timezone
from typing import Optional, Iterator, Any
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DYNAMODB_TABLE_NAME, AWS_REGION


class DynamoDBSaver(BaseCheckpointSaver):
    """
    Checkpointer LangGraph qui persiste la mémoire des conversations
    dans Amazon DynamoDB — équivalent de la mémoire long terme.
    """

    def __init__(self, table_name: str = DYNAMODB_TABLE_NAME, region: str = AWS_REGION):
        super().__init__()
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)

    def _serialize(self, obj: Any) -> str:
        """Sérialise un objet Python en string pour le stockage DynamoDB."""
        return base64.b64encode(pickle.dumps(obj)).decode("utf-8")

    def _deserialize(self, data: str) -> Any:
        """Désérialise une string DynamoDB en objet Python."""
        return pickle.loads(base64.b64decode(data.encode("utf-8")))

    def put(self, config: dict, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict) -> dict:
        """Sauvegarde un checkpoint (état de conversation) dans DynamoDB."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]

        item = {
            "PK": f"THREAD#{thread_id}",
            "SK": f"CHECKPOINT#{checkpoint_id}",
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "checkpoint_data": self._serialize(checkpoint),
            "metadata": self._serialize(metadata),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self.table.put_item(Item=item)

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }

    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """Récupère le dernier checkpoint d'une conversation (thread_id)."""
        thread_id = config["configurable"]["thread_id"]

        response = self.table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": f"THREAD#{thread_id}",
                ":sk_prefix": "CHECKPOINT#"
            },
            ScanIndexForward=False,    # Trie du plus récent au plus ancien
            Limit=1
        )

        items = response.get("Items", [])
        if not items:
            return None

        item = items[0]
        checkpoint = self._deserialize(item["checkpoint_data"])
        metadata = self._deserialize(item["metadata"])

        return CheckpointTuple(
        config=config,
        checkpoint=checkpoint,
        metadata=metadata,
        parent_config=None
    )

    def list(self, config: dict, *, filter: Optional[dict] = None, before: Optional[dict] = None, limit: Optional[int] = None) -> Iterator[CheckpointTuple]:
        """Liste tous les checkpoints d'une conversation."""
        thread_id = config["configurable"]["thread_id"]

        response = self.table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": f"THREAD#{thread_id}",
                ":sk_prefix": "CHECKPOINT#"
            },
            ScanIndexForward=False,
            Limit=limit or 50
        )

        for item in response.get("Items", []):
            checkpoint = self._deserialize(item["checkpoint_data"])
            metadata = self._deserialize(item["metadata"])
        yield CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=None
        )

    def put_writes(self, config: dict, writes: list, task_id: str) -> None:
        """Sauvegarde les écritures intermédiaires (requis par l'interface)."""
        thread_id = config["configurable"]["thread_id"]

        item = {
            "PK": f"THREAD#{thread_id}",
            "SK": f"WRITES#{task_id}",
            "writes_data": self._serialize(writes),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.table.put_item(Item=item)