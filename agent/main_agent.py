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
- obtenir_cours_action / comparer_actions / obtenir_historique_action : pour les cours de bourse

RÈGLES DE RAISONNEMENT :
1. Décompose chaque requête complexe en sous-tâches claires.
2. Utilise plusieurs outils l'un après l'autre si nécessaire pour répondre complètement.
3. Ne réponds jamais de mémoire pour des données factuelles, récentes ou internes — utilise toujours l'outil approprié.
4. Si une information manque pour utiliser un outil, demande une clarification.
5. Formule toujours une réponse finale claire et synthétique en français.
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
    memory = InMemorySaver()

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
                logger.info(f"  THOUGHT/RÉPONSE → {contenu[:200]}")

        elif isinstance(msg, ToolMessage):
            # Résultat retourné par l'outil
            contenu = msg.content if isinstance(msg.content, str) else str(msg.content)
            logger.info(f"  OBSERVATION    → {contenu[:200]}")


def executer_requete(agent, question: str, thread_id: str = "default") -> str:
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


if __name__ == "__main__":
    agent = create_main_agent()

    # Démonstration de la mémoire conversationnelle
    print("\n--- Tour 1 ---")
    reponse1 = executer_requete(agent, "Quel est le cours de l'action Apple ?", thread_id="demo")
    print(reponse1)

    print("\n--- Tour 2 (référence implicite : 'son prix') ---")
    reponse2 = executer_requete(agent, "Et quel est son volume d'échange ?", thread_id="demo")
    print(reponse2)