import boto3
from dotenv import load_dotenv

load_dotenv()

client = boto3.client("bedrock-runtime", region_name="us-east-1")

# Liste des candidats depuis ta liste du ticket 1
models_to_test = [
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    
]

for model_id in models_to_test:
    try:
        response = client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": "Dis bonjour"}]}],
            inferenceConfig={"maxTokens": 50}
        )
        print(f"✅ FONCTIONNE : {model_id}")
        break
    except Exception as e:
        print(f"❌ Échoue : {model_id} → {str(e)[:80]}")