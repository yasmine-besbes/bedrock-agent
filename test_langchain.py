from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os

# Charge le .env
load_dotenv()

# Importe la config
from config.settings import MODEL_ID, AWS_REGION, MODEL_CONFIG


def init_chat_model():
    """
    Instancie la classe ChatBedrock de LangChain.
    C'est le coeur du ticket 2.
    """
    print(f"Initialisation de ChatBedrock...")
    print(f"  Modèle  : {MODEL_ID}")
    print(f"  Région  : {AWS_REGION}")

    llm = ChatBedrock(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
        model_kwargs={
            "temperature": MODEL_CONFIG["temperature"],
            "max_tokens": MODEL_CONFIG["max_tokens"],
        }
    )

    print("ChatBedrock instancié avec succès ✅\n")
    return llm


def test_simple_message(llm):
    """Test 1 : Message simple"""
    print("--- Test 1 : Message simple ---")

    messages = [
        HumanMessage(content="Réponds en une phrase : qu'est-ce que LangChain ?")
    ]

    response = llm.invoke(messages)
    print(f"Réponse : {response.content}\n")
    return True


def test_with_system_prompt(llm):
    """Test 2 : Avec un system prompt"""
    print("--- Test 2 : Avec system prompt ---")

    messages = [
        SystemMessage(content="Tu es un assistant expert en IA. Réponds toujours en français et de façon concise."),
        HumanMessage(content="Explique ce qu'est un agent IA en 2 phrases.")
    ]

    response = llm.invoke(messages)
    print(f"Réponse : {response.content}\n")
    return True


def test_conversation(llm):
    """Test 3 : Conversation multi-tours"""
    print("--- Test 3 : Conversation multi-tours ---")

    from langchain_core.messages import AIMessage

    historique = [
        HumanMessage(content="Mon nom est Yasmine."),
        AIMessage(content="Bonjour Yasmine ! Comment puis-je vous aider ?"),
        HumanMessage(content="Comment tu m'appelles ?")
    ]

    response = llm.invoke(historique)
    print(f"Réponse (doit mentionner Yasmine) : {response.content}\n")
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("  Ticket 2 — Test socle LangChain + ChatBedrock")
    print("=" * 50 + "\n")

    # Instanciation du modèle
    llm = init_chat_model()

    tests_passes = 0

    try:
        if test_simple_message(llm):
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 1 : {e}\n")

    try:
        if test_with_system_prompt(llm):
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 2 : {e}\n")

    try:
        if test_conversation(llm):
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 3 : {e}\n")

    print("=" * 50)
    print(f"Résultat : {tests_passes}/3 tests réussis")

    if tests_passes == 3:
        print("Ticket 2 validé. Prêt pour les Tools et l'Agent !")
    else:
        print("Vérifie le Model ID dans config/settings.py")
    print("=" * 50)