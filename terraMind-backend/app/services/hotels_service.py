from amadeus import Client, ResponseError
import os
from dotenv import load_dotenv
import requests
from unidecode import unidecode

load_dotenv()

AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

# Initialisation du client Amadeus
amadeus = Client(
    client_id=AMADEUS_CLIENT_ID,
    client_secret=AMADEUS_CLIENT_SECRET,
    hostname='test'
)

# Dictionnaire pour convertir les noms de villes en codes IATA
_IATA_FALLBACK = {
    "tanger": "TNG", "barcelone": "BCN", "lisbonne": "LIS", "marrakech": "RAK",
    "casablanca": "CMN", "fes": "FEZ", "new york": "JFK", "londres": "LHR",
    "rome": "FCO", "paris": "CDG", "milan": "MXP", "madrid": "MAD", "bruxelles": "BRU",
    "amsterdam": "AMS", "berlin": "BER", "munich": "MUC", "vienne": "VIE", "prague": "PRG",
    "budapest": "BUD", "varsovie": "WAW", "moscou": "SVO", "istanbul": "IST", "dubaï": "DXB",
    "hong kong": "HKG", "tokyo": "HND", "pekin": "PEK", "shanghai": "PVG", "seoul": "ICN",
    "sydney": "SYD", "melbourne": "MEL", "toronto": "YYZ", "montreal": "YUL", "vancouver": "YVR",
    "rio de janeiro": "GIG", "sao paulo": "GRU", "buenos aires": "EZE", "le cap": "CPT", "nairobi": "NBO",
    "caire": "CAI", "dakar": "DSS", "tunis": "TUN", "alger": "ALG", "beyrouth": "BEY", "delhi": "DEL",
    "bombay": "BOM", "bangalore": "BLR", "chennai": "MAA", "kolkata": "CCU", "singapour": "SIN",
    "kuala lumpur": "KUL", "bangkok": "BKK", "jakarta": "CGK", "manille": "MNL", "athènes": "ATH",
    "oslo": "OSL", "stockholm": "ARN", "helsinki": "HEL", "copenhague": "CPH", "dublin": "DUB",
    "edimbourg": "EDI", "glasgow": "GLA", "manchester": "MAN", "birmingham": "BHX", "nice": "NCE",
    "lyon": "LYS", "toulouse": "TLS", "marseille": "MRS", "geneve": "GVA", "zurich": "ZRH", "francfort": "FRA",
    "hambourg": "HAM", "cologne": "CGN", "venise": "VCE", "florence": "FLR", "naples": "NAP", "bologne": "BLQ",
    "porto": "OPO", "valence": "VLC", "sevilla": "SVQ", "bilbao": "BIO", "malaga": "AGP", "ibiza": "IBZ",
    "palma": "PMI", "las vegas": "LAS", "los angeles": "LAX", "san francisco": "SFO", "chicago": "ORD",
    "miami": "MIA", "washington": "IAD", "boston": "BOS", "philadelphie": "PHL", "atlanta": "ATL", "dallas": "DFW",
    "houston": "IAH", "detroit": "DTW", "phoenix": "PHX", "seattle": "SEA", "calgary": "YYC", "ottawa": "YOW",
    "quebec": "YQB", "edmonton": "YEG", "winnipeg": "YWG", "halifax": "YHZ"
}

# Fonction pour obtenir le token d'authentification de l'API Amadeus
from amadeus import Client
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_amadeus_token():
    auth_url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': os.getenv("AMADEUS_CLIENT_ID"),
        'client_secret': os.getenv("AMADEUS_CLIENT_SECRET")
    }
    response = requests.post(auth_url, data=auth_data)
    if response.status_code == 200:
        return response.json()['access_token']
    raise Exception(f"Erreur d'authentification: {response.text}")


def get_city_code(city_name):
    city_name_normalized = unidecode(city_name.lower())  # Normalisation et suppression des accents
    if city_name_normalized in _IATA_FALLBACK:
        return _IATA_FALLBACK[city_name_normalized]
    else:
        return city_name_normalized  # Si pas de correspondance, utiliser le nom directement


def search_hotels(destination: str, check_in: str, check_out: str, adults: int = 1, rooms: int = 1):
    try:
        # 1. Authentification
        access_token = get_amadeus_token()
        headers = {'Authorization': f'Bearer {access_token}'}

        # 2. Récupération des IDs d'hôtels
        city_code = get_city_code(destination)  # Votre fonction existante
        hotels_list_url = 'https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city'
        hotels_response = requests.get(
            hotels_list_url,
            headers=headers,
            params={'cityCode': city_code}
        )
        
        if hotels_response.status_code != 200:
            return {
                "success": False,
                "error": f"Erreur récupération hôtels: {hotels_response.text}"
            }

        hotel_ids = [hotel['hotelId'] for hotel in hotels_response.json().get('data', [])[:5]]  # Limite à 5 hôtels

        # 3. Recherche des offres
        offers_url = 'https://test.api.amadeus.com/v3/shopping/hotel-offers'
        available_hotels = []
        
        for hotel_id in hotel_ids:
            params = {
                'hotelIds': hotel_id,
                'adults': adults,
                'checkInDate': check_in,
                'checkOutDate': check_out,
                'roomQuantity': rooms
            }

            response = requests.get(offers_url, headers=headers, params=params)
            if response.status_code == 200 and response.json().get("data"):
                available_hotels.append(response.json()["data"][0])

        if not available_hotels:
            return {"success": False, "error": "Aucun hôtel disponible"}

        return {
            "success": True,
            "data": available_hotels,
            "destination": destination
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


