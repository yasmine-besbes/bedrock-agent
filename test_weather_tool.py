from langchain_aws import ChatBedrock
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from config.settings import MODEL_ID, AWS_REGION, MODEL_CONFIG
from tools.weather_tool import obtenir_meteo, obtenir_prevision_meteo, get_coordinates


# ════════════════════════════════════════════════════
# TEST 1 : Géocodage (ville → coordonnées GPS)
# ════════════════════════════════════════════════════
def test_geocodage():
    print("\n--- Test 1 : Géocodage ville → coordonnées ---")

    coords = get_coordinates("Tunis")

    if coords and "latitude" in coords:
        print(f"  Ville trouvée : {coords['nom']}, {coords['pays']}")
        print(f"  Coordonnées : {coords['latitude']}, {coords['longitude']} ✅")
        return True
    else:
        print("  ❌ Géocodage échoué")
        return False


# ════════════════════════════════════════════════════
# TEST 2 : Outil météo actuelle
# ════════════════════════════════════════════════════
def test_meteo_actuelle():
    print("\n--- Test 2 : Outil météo actuelle ---")

    villes = ["Tunis", "Paris", "New York"]
    succes = 0

    for ville in villes:
        resultat = obtenir_meteo.invoke({"ville": ville})
        print(f"\n  {ville} :")
        print(f"  {resultat}")

        if "Erreur" not in resultat:
            succes += 1
        else:
            print(f"  ❌ {resultat}")

    print(f"\n  {succes}/{len(villes)} villes testées avec succès")
    return succes == len(villes)


# ════════════════════════════════════════════════════
# TEST 3 : Outil prévisions météo
# ════════════════════════════════════════════════════
def test_previsions():
    print("\n--- Test 3 : Prévisions météo sur 3 jours ---")

    resultat = obtenir_prevision_meteo.invoke({"ville": "Tunis", "jours": 3})
    print(f"  {resultat}")

    if "Erreur" not in resultat:
        print("  ✅ Prévisions récupérées")
        return True
    else:
        print("  ❌ Échec")
        return False


# ════════════════════════════════════════════════════
# TEST 4 : Gestion des erreurs (ville inexistante)
# ════════════════════════════════════════════════════
def test_ville_invalide():
    print("\n--- Test 4 : Gestion d'erreur ville invalide ---")

    resultat = obtenir_meteo.invoke({"ville": "VilleImaginaireXYZ123"})
    print(f"  Résultat : {resultat}")

    if "Erreur" in resultat or "trouvée" in resultat:
        print("  ✅ Erreur gérée correctement")
        return True
    else:
        print("  ❌ L'erreur n'a pas été gérée")
        return False


# ════════════════════════════════════════════════════
# TEST 5 : Agent extrait les paramètres et appelle l'outil
# ════════════════════════════════════════════════════
def test_agent_meteo():
    print("\n--- Test 5 : Agent extrait paramètres + appelle l'outil ---")

    llm = ChatBedrock(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
        model_kwargs={
            "temperature": 0,
            "max_tokens": 1000,
        }
    )

    tools = [obtenir_meteo, obtenir_prevision_meteo]

    system_prompt = """Tu es un assistant météo qui répond en français.
Quand on te demande la météo d'une ville, utilise l'outil obtenir_meteo
en extrayant le nom de la ville depuis la question de l'utilisateur."""

    agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)

    questions = [
        "Quelle est la météo à Tunis aujourd'hui ?",
        "Donne-moi les prévisions sur 3 jours à Paris",
    ]

    succes = 0
    for question in questions:
        print(f"\n  Question : {question}")
        try:
            resultat = agent.invoke({
                "messages": [HumanMessage(content=question)]
            })
            reponse = resultat["messages"][-1].content
            print(f"  Réponse : {reponse}")
            if reponse and len(reponse) > 10:
                succes += 1
        except Exception as e:
            print(f"  ❌ Erreur : {e}")

    print(f"\n  {succes}/{len(questions)} questions réussies")
    return succes == len(questions)


# ════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("  Ticket 5 — Test Outil API REST Météo")
    print("=" * 55)

    tests_passes = 0
    total_tests = 5

    try:
        if test_geocodage():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 1 : {e}")

    try:
        if test_meteo_actuelle():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 2 : {e}")

    try:
        if test_previsions():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 3 : {e}")

    try:
        if test_ville_invalide():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 4 : {e}")

    try:
        if test_agent_meteo():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 5 : {e}")

    print("\n" + "=" * 55)
    print(f"Résultat : {tests_passes}/{total_tests} tests réussis")

    if tests_passes == total_tests:
        print("Ticket 5 validé. Tous les outils sont prêts !")
    else:
        print("Vérifie les erreurs ci-dessus.")
    print("=" * 55)