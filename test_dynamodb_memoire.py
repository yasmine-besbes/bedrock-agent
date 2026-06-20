import sys
import os
import boto3

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.main_agent import create_main_agent, executer_requete
from config.settings import DYNAMODB_TABLE_NAME, AWS_REGION


# ════════════════════════════════════════════════════
# TEST 1 : La table DynamoDB existe et est accessible
# ════════════════════════════════════════════════════
def test_table_existe():
    print("\n--- Test 1 : Vérification de la table DynamoDB ---")

    try:
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        table.load()

        print(f"  Table : {table.table_name}")
        print(f"  Statut : {table.table_status}")

        if table.table_status == "ACTIVE":
            print("  ✅ La table DynamoDB est active et accessible")
            return True
        else:
            print(f"  ⚠️ La table existe mais n'est pas active : {table.table_status}")
            return False

    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        print(f"  Vérifie que la table '{DYNAMODB_TABLE_NAME}' existe dans la région {AWS_REGION}")
        return False


# ════════════════════════════════════════════════════
# TEST 2 : Une conversation est bien sauvegardée dans DynamoDB
# ════════════════════════════════════════════════════
def test_sauvegarde_dynamodb():
    print("\n--- Test 2 : Sauvegarde d'une conversation dans DynamoDB ---")

    agent = create_main_agent()
    thread_id = "test_persistance_dynamo"

    reponse = executer_requete(
        agent,
        "Mon prénom est Khalil et ma ville préférée est Sousse.",
        thread_id=thread_id
    )
    print(f"  Réponse de l'agent : {reponse}")

    # Vérifie directement dans DynamoDB que l'item a été créé
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)

    response = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": f"THREAD#{thread_id}"}
    )

    items = response.get("Items", [])
    print(f"  Nombre d'items trouvés dans DynamoDB : {len(items)}")

    if len(items) > 0:
        print("  ✅ La conversation a bien été persistée dans DynamoDB")
        return True
    else:
        print("  ❌ Aucune donnée trouvée dans DynamoDB")
        return False


# ════════════════════════════════════════════════════
# TEST 3 : La mémoire survit à un "nouveau" agent (simule un redémarrage)
# ════════════════════════════════════════════════════
def test_persistance_entre_sessions():
    print("\n--- Test 3 : Persistance entre sessions (simulation redémarrage) ---")

    thread_id = "test_redemarrage"

    # ─── Session 1 : on crée un agent et on donne une info ───
    print("\n  Session 1 (premier 'démarrage') :")
    agent_session1 = create_main_agent()
    reponse1 = executer_requete(
        agent_session1,
        "Retiens que mon projet préféré est l'Agent IA Bedrock.",
        thread_id=thread_id
    )
    print(f"  Réponse : {reponse1}")

    # ─── Simule un redémarrage : on recrée un NOUVEL objet agent ───
    print("\n  Session 2 (nouvel objet agent = simule un redémarrage) :")
    agent_session2 = create_main_agent()
    reponse2 = executer_requete(
        agent_session2,
        "Quel est mon projet préféré ?",
        thread_id=thread_id    # Même thread_id = doit retrouver l'historique
    )
    print(f"  Réponse : {reponse2}")

    if "bedrock" in reponse2.lower() or "agent ia" in reponse2.lower():
        print("  ✅ La mémoire a survécu au redémarrage simulé (lecture depuis DynamoDB)")
        return True
    else:
        print("  ❌ La mémoire n'a pas persisté entre les sessions")
        return False


# ════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  Ticket 10 — Test Mémoire Long Terme (DynamoDB)")
    print("=" * 60)

    tests_passes = 0
    total_tests = 3

    try:
        if test_table_existe():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 1 : {e}")

    try:
        if test_sauvegarde_dynamodb():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 2 : {e}")

    try:
        if test_persistance_entre_sessions():
            tests_passes += 1
    except Exception as e:
        print(f"Erreur Test 3 : {e}")

    print("\n" + "=" * 60)
    print(f"Résultat : {tests_passes}/{total_tests} tests réussis")

    if tests_passes == total_tests:
        print("Ticket 10 validé. Mémoire long terme persistante opérationnelle !")
    else:
        print("Vérifie les erreurs ci-dessus.")
    print("=" * 60)