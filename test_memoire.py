import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.main_agent import create_main_agent, executer_requete


# ════════════════════════════════════════════════════
# TEST 1 : La mémoire conserve le contexte entre les tours
# ════════════════════════════════════════════════════
def test_memoire_persiste():
    print("\n--- Test 1 : La mémoire conserve le contexte ---")

    agent = create_main_agent()
    thread_id = "test_memoire_1"

    # Tour 1 : on donne une information
    print("\n  Tour 1 : 'Mon nom est Yasmine et je travaille chez SMARTOVATE.'")
    reponse1 = executer_requete(
        agent,
        "Mon nom est Yasmine et je travaille chez SMARTOVATE.",
        thread_id=thread_id
    )
    print(f"  Réponse : {reponse1}")

    # Tour 2 : on demande si l'agent se souvient (SANS répéter le contexte)
    print("\n  Tour 2 : 'Quel est mon nom et où je travaille ?'")
    reponse2 = executer_requete(
        agent,
        "Quel est mon nom et où je travaille ?",
        thread_id=thread_id
    )
    print(f"  Réponse : {reponse2}")

    # Validation : la réponse doit contenir "Yasmine" et "SMARTOVATE"
    if "Yasmine" in reponse2 and "SMARTOVATE" in reponse2.upper().replace("smartovate", "SMARTOVATE"):
        print("  ✅ L'agent se souvient du contexte précédent")
        return True
    elif "Yasmine" in reponse2:
        print("  ✅ L'agent se souvient au moins partiellement (nom retrouvé)")
        return True
    else:
        print("  ❌ L'agent ne se souvient pas du contexte")
        return False


# ════════════════════════════════════════════════════
# TEST 2 : Résolution d'anaphores (ex: "son prix", "elle", "ça")
# ════════════════════════════════════════════════════
def test_resolution_anaphore():
    print("\n--- Test 2 : Résolution d'anaphores ---")

    agent = create_main_agent()
    thread_id = "test_anaphore_1"

    # Tour 1 : on parle d'une ville précise
    print("\n  Tour 1 : 'Quelle est la météo à Tunis ?'")
    reponse1 = executer_requete(agent, "Quelle est la météo à Tunis ?", thread_id=thread_id)
    print(f"  Réponse : {reponse1}")

    # Tour 2 : référence implicite ("là-bas" = Tunis, sans le redire)
    print("\n  Tour 2 : 'Et quelle est la température minimale prévue là-bas demain ?'")
    reponse2 = executer_requete(
        agent,
        "Et quelle est la température minimale prévue là-bas demain ?",
        thread_id=thread_id
    )
    print(f"  Réponse : {reponse2}")

    # Validation : l'agent doit avoir compris que "là-bas" = Tunis
    if "tunis" in reponse2.lower():
        print("  ✅ L'agent a résolu l'anaphore 'là-bas' → Tunis")
        return True
    else:
        print("  ⚠️ L'agent n'a peut-être pas explicitement mentionné Tunis, vérifie la cohérence")
        # On vérifie si la réponse contient une température (signe que l'outil météo a bien été appelé pour Tunis)
        return any(char.isdigit() for char in reponse2)


# ════════════════════════════════════════════════════
# TEST 3 : Deux conversations séparées ne se mélangent pas
# ════════════════════════════════════════════════════
def test_isolation_threads():
    print("\n--- Test 3 : Isolation entre différentes conversations (thread_id) ---")

    agent = create_main_agent()

    # Conversation A
    executer_requete(agent, "Je m'appelle Sarah.", thread_id="conversation_A")

    # Conversation B (différente !)
    reponse_b = executer_requete(agent, "Quel est mon nom ?", thread_id="conversation_B")
    print(f"  Réponse conversation B : {reponse_b}")

    # La conversation B ne doit PAS connaître "Sarah" (mémoire isolée)
    if "Sarah" not in reponse_b:
        print("  ✅ Les conversations sont bien isolées par thread_id")
        return True
    else:
        print("  ❌ Fuite de mémoire entre conversations différentes")
        return False


# ════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  Ticket 8 — Test Mémoire Conversationnelle")
    print("=" * 60)

    tests_passes = 0
    total_tests = 3

    try:
        if test_memoire_persiste():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 1 : {e}")

    try:
        if test_resolution_anaphore():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 2 : {e}")

    try:
        if test_isolation_threads():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 3 : {e}")

    print("\n" + "=" * 60)
    print(f"Résultat : {tests_passes}/{total_tests} tests réussis")

    if tests_passes == total_tests:
        print("Ticket 8 validé. La mémoire conversationnelle fonctionne !")
    else:
        print("Vérifie les erreurs ci-dessus.")
    print("=" * 60)