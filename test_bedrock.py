import boto3
import json
from dotenv import load_dotenv

load_dotenv()


CLAUDE_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
LLAMA_MODEL_ID  = "meta.llama3-8b-instruct-v1:0"



def test_claude(client):
    print("\n--- Test Claude 4.5 Sonnet ---")

    response = client.converse(
        modelId=CLAUDE_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": "Réponds en une phrase : qu'est-ce qu'un agent IA autonome ?"}
                ]
            }
        ],
        inferenceConfig={
            "maxTokens": 200,
            "temperature": 0.7
        }
    )

    texte = response["output"]["message"]["content"][0]["text"]
    print("Réponse Claude :", texte)
    return True


def test_llama(client):
    print("\n--- Test Llama 3 8B ---")

    response = client.converse(
        modelId=LLAMA_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": "Réponds en une phrase : qu'est-ce qu'un agent IA autonome ?"}
                ]
            }
        ],
        inferenceConfig={
            "maxTokens": 200,
            "temperature": 0.5
        }
    )

    texte = response["output"]["message"]["content"][0]["text"]
    print("Réponse Llama :", texte)
    return True


def list_models():
    print("\n--- Modèles Anthropic et Meta disponibles ---")
    bedrock = boto3.client("bedrock", region_name="us-east-1")
    response = bedrock.list_foundation_models()

    for model in response["modelSummaries"]:
        provider = model.get("providerName", "")
        if provider in ["Anthropic", "Meta"]:
            print(f"  • [{provider}] {model['modelId']}")


if __name__ == "__main__":
    print("Démarrage des tests AWS Bedrock...")

    client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"
    )

    tests_passes = 0

    try:
        if test_claude(client):
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Claude : {e}")

    try:
        if test_llama(client):
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Llama : {e}")

    list_models()

    print(f"\nRésultat final : {tests_passes}/2 tests réussis")

    if tests_passes == 2:
        print("\nTicket 1 validé. Prêt pour LangChain !")
    else:
        print("\nVérifie les Model IDs et les droits IAM.")