import requests
from langchain_core.tools import tool
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import WEATHER_API_URL, GEOCODING_API_URL


def get_coordinates(ville: str) -> dict:
    """
    Convertit le nom d'une ville en coordonnées GPS (latitude, longitude).
    Utilise l'API de géocodage Open-Meteo.
    """
    params = {
        "name": ville,
        "count": 1,
        "language": "fr",
        "format": "json"
    }

    response = requests.get(GEOCODING_API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "results" not in data or len(data["results"]) == 0:
        return None

    resultat = data["results"][0]
    return {
        "nom": resultat["name"],
        "pays": resultat.get("country", "Inconnu"),
        "latitude": resultat["latitude"],
        "longitude": resultat["longitude"]
    }


def get_weather_data(latitude: float, longitude: float) -> dict:
    """
    Récupère les données météo actuelles pour des coordonnées GPS données.
    Utilise l'API Open-Meteo.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "timezone": "auto"
    }

    response = requests.get(WEATHER_API_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def interpreter_code_meteo(code: int) -> str:
    """Convertit le code météo WMO en description textuelle."""
    codes = {
        0: "Ciel dégagé",
        1: "Principalement dégagé",
        2: "Partiellement nuageux",
        3: "Couvert",
        45: "Brouillard",
        48: "Brouillard givrant",
        51: "Bruine légère",
        53: "Bruine modérée",
        55: "Bruine dense",
        61: "Pluie légère",
        63: "Pluie modérée",
        65: "Pluie forte",
        71: "Neige légère",
        73: "Neige modérée",
        75: "Neige forte",
        80: "Averses légères",
        81: "Averses modérées",
        82: "Averses violentes",
        95: "Orage",
        96: "Orage avec grêle légère",
        99: "Orage avec grêle forte"
    }
    return codes.get(code, "Conditions inconnues")


@tool
def obtenir_meteo(ville: str) -> str:
    """
    Récupère la météo actuelle pour une ville donnée.
    Utilise cet outil quand l'utilisateur demande la météo, la température,
    ou les conditions climatiques d'un lieu spécifique.

    Args:
        ville: Le nom de la ville (ex: "Paris", "Tunis", "New York")

    Returns:
        Un résumé textuel de la météo actuelle de la ville
    """
    try:
        # Étape 1 : Convertir le nom de ville en coordonnées GPS
        coords = get_coordinates(ville)

        if coords is None:
            return f"Erreur : la ville '{ville}' n'a pas été trouvée. Vérifie l'orthographe."

        # Étape 2 : Récupérer les données météo
        data = get_weather_data(coords["latitude"], coords["longitude"])

        if "current" not in data:
            return f"Erreur : aucune donnée météo disponible pour {ville}."

        current = data["current"]

        # Étape 3 : Parser et formater la réponse JSON
        temperature = current.get("temperature_2m", "N/A")
        humidite = current.get("relative_humidity_2m", "N/A")
        vent = current.get("wind_speed_10m", "N/A")
        code_meteo = current.get("weather_code", -1)
        description = interpreter_code_meteo(code_meteo)

        resultat = (
            f"Météo actuelle à {coords['nom']}, {coords['pays']} :\n"
            f"- Conditions : {description}\n"
            f"- Température : {temperature}°C\n"
            f"- Humidité : {humidite}%\n"
            f"- Vent : {vent} km/h"
        )

        return resultat

    except requests.exceptions.Timeout:
        return "Erreur : le service météo n'a pas répondu à temps."
    except requests.exceptions.RequestException as e:
        return f"Erreur de connexion à l'API météo : {str(e)}"
    except Exception as e:
        return f"Erreur inattendue : {str(e)}"


@tool
def obtenir_prevision_meteo(ville: str, jours: int = 3) -> str:
    """
    Récupère les prévisions météo sur plusieurs jours pour une ville donnée.

    Args:
        ville: Le nom de la ville
        jours: Le nombre de jours de prévision (1 à 7, par défaut 3)

    Returns:
        Un résumé des prévisions météo
    """
    try:
        jours = max(1, min(jours, 7))  # Sécurise entre 1 et 7

        coords = get_coordinates(ville)
        if coords is None:
            return f"Erreur : la ville '{ville}' n'a pas été trouvée."

        params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "timezone": "auto",
            "forecast_days": jours
        }

        response = requests.get(WEATHER_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        codes = daily.get("weather_code", [])

        resultat = f"Prévisions météo pour {coords['nom']}, {coords['pays']} :\n"
        for i in range(len(dates)):
            description = interpreter_code_meteo(codes[i])
            resultat += (
                f"- {dates[i]} : {description}, "
                f"min {temp_min[i]}°C / max {temp_max[i]}°C\n"
            )

        return resultat

    except Exception as e:
        return f"Erreur lors de la récupération des prévisions : {str(e)}"