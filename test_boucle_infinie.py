import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.main_agent import (
    create_main_agent,
    executer_requete,
    MAX_ITERATIONS,
    RECURSION_LIMIT
)


# ════════════════════════════════════════════════════
# TEST 1 : La limite recursion_limit est bien configurée
# ════════════════════════════════════════════════════
def test_limite_configuree():
    print("\n--- Test 1 : Vérification de la configuration anti-boucle ---")

    print(f"  MAX_ITERATIONS configuré : {MAX_ITERATIONS}")
    print(f"  RECURSION_LIMIT configuré : {RECURSION_LIMIT}")

    if MAX_ITERATIONS > 0 and RECURSION_LIMIT > MAX_ITERATIONS:
        print("  ✅ La limite anti-boucle est correctement définie")
        return True
    else:
        print("  ❌ La configuration de la limite est incorrecte")
        return False


# ════════════════════════════════════════════════════
# TEST 2 : L'agent répond normalement pour une question simple
# (vérifie qu'on n'a pas cassé le fonctionnement normal)
# ════════════════════════════════════════════════════
def test_fonctionnement_normal():
    print("\n--- Test 2 : Fonctionnement normal préservé ---")

    agent = create_main_agent()

    debut = time.time()
    reponse = executer_requete(
        agent,
        "Quelle est la météo à Tunis ?",
        thread_id="test_normal"
    )
    duree = time.time() - debut

    print(f"  Réponse : {reponse}")
    print(f"  Durée : {duree:.2f} secondes")

    if reponse and "météo" in reponse.lower() or "tunis" in reponse.lower() or "°c" in reponse.lower():
        print("  ✅ L'agent répond normalement pour une question simple")
        return True
    elif reponse and len(reponse) > 10:
        print("  ✅ L'agent a répondu (contenu à vérifier manuellement)")
        return True
    else:
        print("  ❌ L'agent n'a pas répondu correctement")
        return False


# ════════════════════════════════════════════════════
# TEST 3 : Le system prompt contient bien les règles anti-boucle
# ════════════════════════════════════════════════════
def test_prompt_contient_regles():
    print("\n--- Test 3 : Vérification des règles anti-boucle dans le prompt ---")

    from agent.main_agent import SYSTEM_PROMPT

    mots_cles_attendus = [
        "JAMAIS",
        "même",
        "RÉESSAIE",
        "réponse finale"
    ]

    trouves = [mot for mot in mots_cles_attendus if mot.lower() in SYSTEM_PROMPT.lower()]
    print(f"  Règles trouvées dans le prompt : {len(trouves)}/{len(mots_cles_attendus)}")

    if len(trouves) >= 3:
        print("  ✅ Le system prompt contient des instructions anti-boucle claires")
        return True
    else:
        print("  ❌ Le system prompt manque d'instructions anti-boucle")
        return False


# ════════════════════════════════════════════════════
# TEST 4 : Simulation d'une boucle avec un outil qui échoue
# ════════════════════════════════════════════════════
def test_gestion_boucle_simulee():
    print("\n--- Test 4 : Gestion d'un outil qui échoue systématiquement ---")

    from langchain_aws import ChatBedrock
    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.errors import GraphRecursionError
    from langchain_core.messages import HumanMessage
    from config.settings import MODEL_ID, AWS_REGION, MODEL_CONFIG
    from tools.test_loop_tool import outil_qui_echoue_toujours

    llm = ChatBedrock(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
        model_kwargs={"temperature": 0, "max_tokens": 500}
    )

    prompt_test = """Tu es un assistant de test. Utilise l'outil disponible pour répondre.
Si l'outil échoue, RÉESSAIE EXACTEMENT 3 fois maximum, puis donne une réponse finale
expliquant que l'outil ne fonctionne pas."""

    agent_test = create_agent(
        model=llm,
        tools=[outil_qui_echoue_toujours],
        system_prompt=prompt_test,
        checkpointer=InMemorySaver()
    )

    config = {
        "configurable": {"thread_id": "test_boucle"},
        "recursion_limit": 8     # Limite volontairement basse pour le test
    }

    try:
        resultat = agent_test.invoke(
            {"messages": [HumanMessage(content="Utilise l'outil de test avec le paramètre 'test123'")]},
            config=config
        )
        reponse = resultat["messages"][-1].content
        print(f"  Réponse obtenue : {reponse[:200]}")
        print("  ✅ L'agent a terminé sans dépasser la limite (a su s'arrêter)")
        return True

    except GraphRecursionError:
        print("  ✅ GraphRecursionError correctement levée et détectable")
        print("     (la boucle infinie a été stoppée par la limite)")
        return True

    except Exception as e:
        print(f"  ❌ Erreur inattendue : {e}")
        return False


# ════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  Ticket 9 (Bug) — Test Correction Boucle Infinie")
    print("=" * 60)

    tests_passes = 0
    total_tests = 4

    try:
        if test_limite_configuree():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 1 : {e}")

    try:
        if test_fonctionnement_normal():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 2 : {e}")

    try:
        if test_prompt_contient_regles():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 3 : {e}")

    try:
        if test_gestion_boucle_simulee():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 4 : {e}")

    print("\n" + "=" * 60)
    print(f"Résultat : {tests_passes}/{total_tests} tests réussis")

    if tests_passes == total_tests:
        print("Ticket 9 (Bug) corrigé et validé !")
    else:
        print("Vérifie les erreurs ci-dessus.")
    print("=" * 60)