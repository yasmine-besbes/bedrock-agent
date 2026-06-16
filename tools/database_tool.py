from langchain_community.utilities import SQLDatabase
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DATABASE_URL, DB_PATH


def get_database():
    """Retourne une instance SQLDatabase de LangChain."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Base de données introuvable : {DB_PATH}\n"
            f"Lance d'abord : python data/create_database.py"
        )

    db = SQLDatabase.from_uri(
        DATABASE_URL,
        include_tables=["employes", "projets", "ventes"],
        sample_rows_in_table_info=3      # Montre 3 exemples de lignes à l'agent
    )
    return db


def get_db_info():
    """Retourne les informations sur la structure de la base."""
    db = get_database()
    return db.get_table_info()


@tool
def interroger_base_de_donnees(question: str) -> str:
    """
    Interroge la base de données de l'entreprise en langage naturel.
    Utilise cet outil pour répondre à des questions sur :
    - Les employés (salaires, départements, postes)
    - Les projets (statuts, budgets, responsables)
    - Les ventes (montants, clients, vendeurs)

    Args:
        question: La question en langage naturel sur les données de l'entreprise

    Returns:
        La réponse basée sur les données de la base
    """
    try:
        from langchain_aws import ChatBedrock
        from langchain_community.agent_toolkits import create_sql_agent
        from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

        from config.settings import MODEL_ID, AWS_REGION, MODEL_CONFIG

        # Connexion à la base
        db = get_database()

        # Modèle LLM
        llm = ChatBedrock(
            model_id=MODEL_ID,
            region_name=AWS_REGION,
            model_kwargs={
                "temperature": 0,
                "max_tokens": 1000,
            }
        )

        # Toolkit SQL
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)

        # Agent SQL
        agent = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            verbose=False,
            max_iterations=10,
            handle_parsing_errors=True,
            agent_type="tool-calling"
        )

        resultat = agent.invoke({"input": question})
        return resultat.get("output", "Aucune réponse générée.")

    except Exception as e:
        return f"Erreur lors de l'interrogation : {str(e)}"


@tool
def executer_sql(query: str) -> str:
    """
    Exécute une requête SQL en lecture seule sur la base de données.
    Utilise cet outil uniquement pour des requêtes SELECT.

    Args:
        query: La requête SQL SELECT à exécuter

    Returns:
        Les résultats de la requête en format texte
    """
    try:
        # Sécurité : lecture seule uniquement
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            return "Erreur : Seules les requêtes SELECT sont autorisées."

        mots_interdits = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE"]
        for mot in mots_interdits:
            if mot in query_upper:
                return f"Erreur : La commande {mot} n'est pas autorisée."

        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            columns = list(result.keys())

            if not rows:
                return "Aucun résultat trouvé."

            # Formate les résultats
            output = f"Colonnes : {', '.join(columns)}\n"
            output += "-" * 50 + "\n"
            for row in rows:
                output += " | ".join(str(val) for val in row) + "\n"
            output += f"\nTotal : {len(rows)} ligne(s)"

            return output

    except Exception as e:
        return f"Erreur SQL : {str(e)}"