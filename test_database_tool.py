from langchain_aws import ChatBedrock
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from config.settings import MODEL_ID, AWS_REGION, MODEL_CONFIG
from tools.database_tool import (
    interroger_base_de_donnees,
    executer_sql,
    get_db_info
)


# ════════════════════════════════════════════════════
# TEST 1 : Structure de la base de données
# ════════════════════════════════════════════════════
def test_structure_db():
    print("\n--- Test 1 : Structure de la base de données ---")

    try:
        info = get_db_info()
        print(f"Structure reçue ({len(info)} caractères) ✅")
        print(f"Aperçu :\n{info[:500]}...")
        return True
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False


# ════════════════════════════════════════════════════
# TEST 2 : Requêtes SQL directes
# ════════════════════════════════════════════════════
def test_requetes_sql():
    print("\n--- Test 2 : Requêtes SQL directes ---")

    requetes = [
        ("Tous les employés du département Tech",
         "SELECT prenom, nom, poste, salaire FROM employes WHERE departement = 'Tech'"),

        ("Projets en cours",
         "SELECT nom, client, budget, responsable FROM projets WHERE statut = 'En cours'"),

        ("Total des ventes payées",
         "SELECT SUM(montant) as total_ventes FROM ventes WHERE statut = 'Payé'"),
    ]

    succes = 0
    for description, query in requetes:
        print(f"\n  → {description}")
        resultat = executer_sql.invoke({"query": query})
        if "Erreur" not in resultat:
            print(f"  {resultat[:200]}")
            succes += 1
        else:
            print(f"  ❌ {resultat}")

    print(f"\n  {succes}/{len(requetes)} requêtes réussies")
    return succes == len(requetes)


# ════════════════════════════════════════════════════
# TEST 3 : Sécurité lecture seule
# ════════════════════════════════════════════════════
def test_securite():
    print("\n--- Test 3 : Sécurité lecture seule ---")

    requetes_interdites = [
        "DELETE FROM employes WHERE id = 1",
        "DROP TABLE ventes",
        "INSERT INTO employes VALUES (1,'test','test','test','test',0,'2024-01-01','test')",
        "UPDATE employes SET salaire = 0",
    ]

    succes = 0
    for query in requetes_interdites:
        resultat = executer_sql.invoke({"query": query})
        if "Erreur" in resultat or "autorisée" in resultat or "autorisées" in resultat:
            print(f"  ✅ Bloqué : {query[:50]}...")
            succes += 1
        else:
            print(f"  ❌ Non bloqué : {query[:50]}...")

    print(f"\n  {succes}/{len(requetes_interdites)} requêtes bloquées")
    return succes == len(requetes_interdites)


# ════════════════════════════════════════════════════
# TEST 4 : Agent qui répond en langage naturel
# ════════════════════════════════════════════════════
def test_agent_sql():
    print("\n--- Test 4 : Agent langage naturel → SQL ---")

    llm = ChatBedrock(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
        model_kwargs={
            "temperature": 0,
            "max_tokens": 1000,
        }
    )

    tools = [interroger_base_de_donnees, executer_sql]

    system_prompt = """Tu es un assistant IA expert en données d'entreprise.
Tu réponds toujours en français.
Pour toute question sur les employés, projets ou ventes, utilise les outils disponibles.
Ne réponds jamais de mémoire pour les données de l'entreprise."""

    agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)

    questions = [
        "Combien d'employés travaillent dans le département Tech ?",
        "Quel est le budget total des projets en cours ?",
    ]

    succes = 0
    for question in questions:
        print(f"\n  Question : {question}")
        try:
            resultat = agent.invoke({
                "messages": [HumanMessage(content=question)]
            })
            reponse = resultat["messages"][-1].content
            print(f"  Réponse : {reponse[:300]}")
            if reponse and len(reponse) > 10:
                succes += 1
        except Exception as e:
            print(f"  ❌ Erreur : {e}")

    print(f"\n  {succes}/{len(questions)} questions répondues")
    return succes == len(questions)


# ════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("  Ticket 4 — Test Outil Base de Données SQL")
    print("=" * 55)

    tests_passes = 0

    try:
        if test_structure_db():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 1 : {e}")

    try:
        if test_requetes_sql():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 2 : {e}")

    try:
        if test_securite():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 3 : {e}")

    try:
        if test_agent_sql():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 4 : {e}")

    print("\n" + "=" * 55)
    print(f"Résultat : {tests_passes}/4 tests réussis")

    if tests_passes == 4:
        print("Ticket 4 validé. Prêt pour la mémoire !")
    elif tests_passes >= 3:
        print("Ticket 4 quasi validé — vérifie le test en erreur.")
    else:
        print("Vérifie les erreurs ci-dessus.")
    print("=" * 55)