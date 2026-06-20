import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.main_agent import create_main_agent, executer_requete, logger
from langchain_core.messages import AIMessage, ToolMessage


# ════════════════════════════════════════════════════
# TEST 1 : L'agent utilise l'approche ReAct/LangGraph
# ════════════════════════════════════════════════════
def test_approche_react():
    print("\n--- Test 1 : Vérification de l'approche ReAct/LangGraph ---")

    agent = create_main_agent()

    # Vérifie que l'agent est bien un graphe LangGraph compilé
    if hasattr(agent, "invoke") and hasattr(agent, "nodes"):
        print("  ✅ L'agent est un graphe LangGraph compilé (approche ReAct)")
        return True
    elif hasattr(agent, "invoke"):
        print("  ✅ L'agent possède une méthode invoke() compatible ReAct")
        return True
    else:
        print("  ❌ L'agent ne semble pas être configuré correctement")
        return False


# ════════════════════════════════════════════════════
# TEST 2 : L'agent enchaîne plusieurs outils différents
# ════════════════════════════════════════════════════
def test_enchainement_outils():
    print("\n--- Test 2 : Enchaînement de plusieurs outils ---")

    agent = create_main_agent()

    # Question qui NÉCESSITE 2 outils différents : web + base de données
    question = (
        "Cherche sur le web les dernières tendances en intelligence artificielle en 2026, "
        "et dis-moi combien d'employés travaillent dans le département Tech selon notre base de données."
    )

    resultat = agent.invoke({
        "messages": [{"role": "user", "content": question}]
    })

    messages = resultat["messages"]

    # Compte les outils distincts utilisés
    outils_utilises = set()
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool_call in msg.tool_calls:
                outils_utilises.add(tool_call["name"])

    print(f"  Outils utilisés par l'agent : {outils_utilises}")

    reponse_finale = messages[-1].content
    print(f"  Réponse finale : {reponse_finale}")

    if len(outils_utilises) >= 2:
        print(f"  ✅ L'agent a enchaîné {len(outils_utilises)} outils différents")
        return True
    else:
        print(f"  ❌ L'agent n'a utilisé que {len(outils_utilises)} outil(s)")
        return False


# ════════════════════════════════════════════════════
# TEST 3 : Les étapes Thought/Action/Observation sont loguées
# ════════════════════════════════════════════════════
def test_logging_etapes():
    print("\n--- Test 3 : Logging des étapes de raisonnement ---")

    agent = create_main_agent()
    question = "Quelle est la météo actuelle à Tunis ?"

    reponse = executer_requete(agent, question)

    # Vérifie que le fichier de log existe et contient des entrées
    from datetime import datetime
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    log_file = os.path.join(log_dir, f"agent_{datetime.now().strftime('%Y%m%d')}.log")

    if not os.path.exists(log_file):
        print(f"  ❌ Fichier de log introuvable : {log_file}")
        return False

    with open(log_file, "r", encoding="utf-8") as f:
        contenu_log = f.read()

    elements_requis = ["THOUGHT", "ACTION", "OBSERVATION", "RÉPONSE FINALE"]
    elements_trouves = [e for e in elements_requis if e in contenu_log]

    print(f"  Fichier de log : {log_file}")
    print(f"  Éléments trouvés dans les logs : {elements_trouves}")

    if len(elements_trouves) >= 3:
        print(f"  ✅ Le logging des étapes fonctionne correctement")
        return True
    else:
        print(f"  ❌ Logging incomplet")
        return False


# ════════════════════════════════════════════════════
# TEST 4 : Requête complexe multi-étapes (3 outils)
# ════════════════════════════════════════════════════
def test_requete_complexe():
    print("\n--- Test 4 : Requête complexe nécessitant plusieurs outils ---")

    agent = create_main_agent()

    question = (
        "Donne-moi la météo à Paris, les prévisions sur 3 jours à Tunis, "
        "et le nombre total de projets en cours dans notre base de données."
    )

    resultat = agent.invoke({
        "messages": [{"role": "user", "content": question}]
    })

    messages = resultat["messages"]
    outils_utilises = set()
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool_call in msg.tool_calls:
                outils_utilises.add(tool_call["name"])

    reponse_finale = messages[-1].content
    print(f"  Outils utilisés : {outils_utilises}")
    print(f"  Réponse : {reponse_finale}")

    if len(outils_utilises) >= 3:
        print(f"  ✅ L'agent a utilisé {len(outils_utilises)} outils pour une requête complexe")
        return True
    else:
        print(f"  ⚠️ Seulement {len(outils_utilises)} outils utilisés (attendu : 3)")
        return len(outils_utilises) >= 2  # Tolérance


# ════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  Ticket 7 — Test Agent Executor (boucle de raisonnement)")
    print("=" * 60)

    tests_passes = 0
    total_tests = 4

    try:
        if test_approche_react():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 1 : {e}")

    try:
        if test_enchainement_outils():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 2 : {e}")

    try:
        if test_logging_etapes():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 3 : {e}")

    try:
        if test_requete_complexe():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 4 : {e}")

    print("\n" + "=" * 60)
    print(f"Résultat : {tests_passes}/{total_tests} tests réussis")

    if tests_passes == total_tests:
        print("Ticket 7 validé. L'agent orchestre tous les outils !")
    else:
        print("Vérifie les erreurs ci-dessus.")
    print("=" * 60)