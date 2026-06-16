from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from dotenv import load_dotenv
import os
import sys

# Ajoute le dossier parent au path pour importer config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import SEARCH_CONFIG, TAVILY_API_KEY

load_dotenv()


def create_search_tool():
    """
    Crée et retourne l'outil de recherche web.
    Utilise DuckDuckGo par défaut, Tavily si la clé API est fournie.
    """

    # ─── Option 1 : Tavily (si clé API disponible) ───────────────────
    if TAVILY_API_KEY:
        print("Outil de recherche : Tavily")
        from langchain_community.tools.tavily_search import TavilySearchResults
        search_tool = TavilySearchResults(
            max_results=SEARCH_CONFIG["max_results"],
            description=(
                "Outil de recherche web. "
                "Utilise cet outil pour trouver des informations récentes sur internet. "
                "Entrée : une question ou des mots-clés en string. "
                "Sortie : un résumé des résultats trouvés."
            )
        )
        return search_tool

    # ─── Option 2 : DuckDuckGo (par défaut, sans clé API) ────────────
    print("Outil de recherche : DuckDuckGo")

    wrapper = DuckDuckGoSearchAPIWrapper(
        max_results=SEARCH_CONFIG["max_results"],
        region=SEARCH_CONFIG["region"],
        time="y",       # Résultats de l'année en cours
        safesearch="moderate"
    )

    search_tool = DuckDuckGoSearchRun(
        api_wrapper=wrapper,
        name="recherche_web",
        description=(
            "Outil de recherche web. "
            "Utilise cet outil pour trouver des informations récentes sur internet. "
            "Entrée : une question ou des mots-clés en string. "
            "Sortie : un résumé des résultats trouvés."
        )
    )

    return search_tool


# Outil décoré LangChain (version alternative avec @tool)
@tool
def recherche_web(query: str) -> str:
    """
    Effectue une recherche web et retourne un résumé des résultats.
    Utilise cet outil quand tu as besoin d'informations récentes ou actuelles.

    Args:
        query: La question ou les mots-clés à rechercher

    Returns:
        Un résumé des résultats de recherche
    """
    try:
        wrapper = DuckDuckGoSearchAPIWrapper(
            max_results=SEARCH_CONFIG["max_results"],
            region=SEARCH_CONFIG["region"],
            time="y",
            safesearch="moderate"
        )
        search = DuckDuckGoSearchRun(api_wrapper=wrapper)
        resultat = search.run(query)

        if not resultat:
            return "Aucun résultat trouvé pour cette recherche."

        return resultat

    except Exception as e:
        return f"Erreur lors de la recherche : {str(e)}"