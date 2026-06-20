from langchain_core.tools import tool


@tool
def outil_qui_echoue_toujours(parametre: str) -> str:
    """
    Outil de TEST qui échoue toujours volontairement.
    Utilisé uniquement pour vérifier que l'agent ne boucle pas à l'infini
    quand un outil ne fonctionne jamais.

    Args:
        parametre: N'importe quelle valeur de test

    Returns:
        Toujours un message d'erreur
    """
    return "ERREUR : Cet outil échoue toujours (test de boucle infinie)."