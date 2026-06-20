import sys
import os
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_aws import ChatBedrock
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from dotenv import load_dotenv

load_dotenv()

from config.settings import MODEL_ID, AWS_REGION, MODEL_CONFIG
from tools.search_tool import recherche_web
from tools.database_tool import interroger_base_de_donnees, executer_sql
from tools.weather_tool import obtenir_meteo, obtenir_prevision_meteo

from langgraph.checkpoint.memory import InMemorySaver

from langgraph.errors import GraphRecursionError
# Limite d'itérations pour éviter les boucles infinies (équivalent max_iterations)
MAX_ITERATIONS = 10
RECURSION_LIMIT = MAX_ITERATIONS * 2 + 1  # LangGraph compte chaque étape (action + observation)

from agent.dynamodb_checkpointer import DynamoDBSaver
# ════════════════════════════════════════════════════
# CONFIGURATION DU LOGGING
# ════════════════════════════════════════════════════
def setup_logger():
    """Configure le logger pour tracer Thought/Action/Observation."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"agent_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger("agent_executor")
    logger.setLevel(logging.INFO)

    # Évite les doublons de handlers si la fonction est appelée plusieurs fois
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(console_handler)

    return logger


logger = setup_logger()


# ════════════════════════════════════════════════════
# SYSTEM PROMPT — comportement de l'agent
# ════════════════════════════════════════════════════
SYSTEM_PROMPT = """Tu es un agent IA autonome et polyvalent qui répond toujours en français.

Tu as accès à plusieurs outils :
- recherche_web : pour trouver des informations récentes sur internet
- interroger_base_de_donnees / executer_sql : pour les données internes de l'entreprise (employés, projets, ventes)
- obtenir_meteo / obtenir_prevision_meteo : pour la météo d'une ville

RÈGLES DE RAISONNEMENT :
1. Décompose chaque requête complexe en sous-tâches claires.
2. Utilise plusieurs outils l'un après l'autre si nécessaire pour répondre complètement.
3. Ne réponds jamais de mémoire pour des données factuelles, récentes ou internes — utilise toujours l'outil approprié.
4. Si une information manque pour utiliser un outil, demande une clarification au lieu d'essayer plusieurs fois.

RÈGLES STRICTES ANTI-BOUCLE (TRÈS IMPORTANT) :
5. N'appelle JAMAIS le même outil avec EXACTEMENT les mêmes paramètres plus d'une fois.
6. Si un outil retourne une erreur ou un résultat vide, NE RÉESSAIE PAS la même requête.
   Formule immédiatement une réponse finale expliquant le problème à l'utilisateur.
7. Si après 2 tentatives avec un outil tu n'obtiens pas l'information souhaitée,
   ARRÊTE d'utiliser cet outil et donne une réponse finale avec les informations
   disponibles, même partielles.
8. Tu DOIS toujours te terminer par une réponse finale claire en français.
   Ne jamais laisser une conversation sans réponse finale.
9. Si tu sens que tu tournes en rond ou répètes la même action, arrête-toi
   immédiatement et explique à l'utilisateur ce qui s'est passé.
"""


def create_main_agent():
    """Crée et retourne l'agent principal avec tous les outils + mémoire conversationnelle."""

    llm = ChatBedrock(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
        model_kwargs={
            "temperature": MODEL_CONFIG["temperature"],
            "max_tokens": MODEL_CONFIG["max_tokens"],
        }
    )

    tools = [
        recherche_web,
        interroger_base_de_donnees,
        executer_sql,
        obtenir_meteo,
        obtenir_prevision_meteo,
    ]

    # ─── Mémoire conversationnelle ───
    #memory = InMemorySaver()
    memory = DynamoDBSaver()

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=memory
    )

    logger.info(
        f"Agent créé avec {len(tools)} outils et mémoire conversationnelle activée"
    )

    return agent


def log_etapes_raisonnement(messages):
    """
    Parcourt les messages de l'agent et logue chaque étape
    Thought / Action / Observation.
    """
    for msg in messages:
        if isinstance(msg, AIMessage):
            # Si l'IA a décidé d'utiliser un outil
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    logger.info(f"  THOUGHT/ACTION → Outil appelé : {tool_call['name']}")
                    logger.info(f"  ACTION INPUT   → Paramètres : {tool_call['args']}")
            # Si l'IA a un contenu textuel (réflexion ou réponse finale)
            if msg.content:
                contenu = msg.content if isinstance(msg.content, str) else str(msg.content)
                logger.info(f"  THOUGHT/RÉPONSE → {contenu}")

        elif isinstance(msg, ToolMessage):
            # Résultat retourné par l'outil
            contenu = msg.content if isinstance(msg.content, str) else str(msg.content)
            logger.info(f"  OBSERVATION    → {contenu}")


def executer_requete1(agent, question: str, thread_id: str = "default") -> str:
    """
    Exécute une requête sur l'agent en conservant la mémoire de la conversation.
    Le thread_id identifie une conversation unique (ex: un utilisateur ou une session).
    """
    logger.info("=" * 60)
    logger.info(f"NOUVELLE REQUÊTE [thread: {thread_id}] : {question}")
    logger.info("=" * 60)

    config = {"configurable": {"thread_id": thread_id}}

    resultat = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config=config
    )

    messages = resultat["messages"]
    log_etapes_raisonnement(messages)

    reponse_finale = messages[-1].content

    logger.info(f"RÉPONSE FINALE : {reponse_finale}")
    logger.info("=" * 60 + "\n")

    return reponse_finale

def executer_requete(agent, question: str, thread_id: str = "default") -> str:
    """
    Exécute une requête sur l'agent avec une limite stricte d'itérations
    pour éviter les boucles infinies (équivalent max_iterations).
    """
    logger.info("=" * 60)
    logger.info(f"NOUVELLE REQUÊTE [thread: {thread_id}] : {question}")
    logger.info("=" * 60)

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": RECURSION_LIMIT     # ← Limite anti-boucle infinie
    }

    try:
        resultat = agent.invoke(
            {"messages": [HumanMessage(content=question)]},
            config=config
        )

        messages = resultat["messages"]
        log_etapes_raisonnement(messages)

        reponse_finale = messages[-1].content

        # Sécurité supplémentaire : si la réponse finale est vide
        if not reponse_finale or len(reponse_finale.strip()) == 0:
            reponse_finale = (
                "Je n'ai pas pu formuler de réponse complète. "
                "Pouvez-vous reformuler votre question ?"
            )
            logger.warning("Réponse finale vide détectée — message de secours utilisé")

        logger.info(f"RÉPONSE FINALE : {reponse_finale}")
        logger.info("=" * 60 + "\n")

        return reponse_finale

    except GraphRecursionError:
        # L'agent a dépassé la limite d'itérations → boucle infinie détectée
        message_erreur = (
            "Je n'ai pas pu obtenir de réponse définitive après plusieurs tentatives "
            "(limite d'itérations atteinte). Cela peut arriver si la question est trop "
            "complexe ou si un outil ne répond pas correctement. "
            "Essayez de reformuler votre question de façon plus simple."
        )
        logger.error(
            f"BOUCLE INFINIE DÉTECTÉE — limite de {MAX_ITERATIONS} itérations atteinte "
            f"pour la question : {question}"
        )
        logger.info("=" * 60 + "\n")
        return message_erreur

    except Exception as e:
        message_erreur = f"Une erreur inattendue s'est produite : {str(e)}"
        logger.error(f"ERREUR : {e}")
        logger.info("=" * 60 + "\n")
        return message_erreur


if __name__ == "__main__":
    agent = create_main_agent()

    # Démonstration de la mémoire conversationnelle
    print("\n--- Tour 1 ---")
    reponse1 = executer_requete(agent, "Quel est le cours de l'action Apple ?", thread_id="demo")
    print(reponse1)

    print("\n--- Tour 2 (référence implicite : 'son prix') ---")
    reponse2 = executer_requete(agent, "Et quel est son volume d'échange ?", thread_id="demo")
    print(reponse2)