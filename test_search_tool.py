from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from config.settings import MODEL_ID, AWS_REGION, MODEL_CONFIG
from tools.search_tool import create_search_tool, recherche_web


# ════════════════════════════════════════════════════
# TEST 1 : L'outil fonctionne seul (sans agent)
# ════════════════════════════════════════════════════
def test_outil_seul():
    print("\n--- Test 1 : Outil de recherche seul ---")

    tool = create_search_tool()
    query = "Dernières nouvelles intelligence artificielle 2025"
    print(f"Requête : {query}")

    resultat = tool.run(query)

    if resultat and len(resultat) > 50:
        print(f"Résultat reçu ({len(resultat)} caractères) ✅")
        print(f"Aperçu : {resultat[:300]}...")
        return True
    else:
        print(f"Résultat vide ❌ : {resultat}")
        return False


# ════════════════════════════════════════════════════
# TEST 2 : L'outil décoré @tool fonctionne
# ════════════════════════════════════════════════════
def test_outil_decore():
    print("\n--- Test 2 : Outil @tool LangChain ---")

    print(f"Nom de l'outil   : {recherche_web.name}")
    print(f"Description      : {recherche_web.description[:80]}...")

    resultat = recherche_web.invoke({"query": "actualités IA 2025"})

    if resultat and len(resultat) > 50:
        print(f"Résultat reçu ✅")
        print(f"Aperçu : {resultat[:300]}...")
        return True
    else:
        print(f"Résultat vide ❌")
        return False


# ════════════════════════════════════════════════════
# TEST 3 : L'agent décide d'utiliser l'outil
# ════════════════════════════════════════════════════
def test_agent_avec_outil():
    print("\n--- Test 3 : Agent LangGraph qui utilise l'outil ---")

    llm = ChatBedrock(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
        model_kwargs={
            "temperature": MODEL_CONFIG["temperature"],
            "max_tokens": MODEL_CONFIG["max_tokens"],
        }
    )

    tools = [recherche_web]

    # Prompt système pour l'agent
    system_prompt = """Tu es un assistant IA utile qui répond toujours en français.
Quand on te pose une question sur l'actualité ou des événements récents,
tu DOIS utiliser l'outil de recherche web pour trouver des informations à jour.
Ne réponds jamais de mémoire pour les questions d'actualité."""

    # Création de l'agent LangGraph 1.x
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt
    )

    question = "Quelles sont les dernières actualités sur l'intelligence artificielle en 2025 ?"
    print(f"\nQuestion posée à l'agent : {question}\n")

    resultat = agent.invoke({
        "messages": [HumanMessage(content=question)]
    })

    # Récupère le dernier message
    reponse_finale = resultat["messages"][-1].content
    print(f"\nRéponse finale : {reponse_finale}")

    if reponse_finale and len(reponse_finale) > 20:
        return True
    return False


# ════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("  Ticket 3 — Test Outil Recherche Web + Agent")
    print("=" * 55)

    tests_passes = 0

    try:
        if test_outil_seul():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 1 : {e}")

    try:
        if test_outil_decore():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 2 : {e}")

    try:
        if test_agent_avec_outil():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 3 : {e}")

    print("\n" + "=" * 55)
    print(f"Résultat : {tests_passes}/3 tests réussis")

    if tests_passes == 3:
        print("Ticket 3 validé. Prêt pour les outils suivants !")
    else:
        print("Vérifie les erreurs ci-dessus.")
    print("=" * 55)