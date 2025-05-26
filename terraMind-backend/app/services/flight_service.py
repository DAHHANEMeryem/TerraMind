from amadeus import Client, ResponseError
import os
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode
from unidecode import unidecode
import re
from datetime import datetime
import dateparser
from typing import Optional

load_dotenv()

# Configuration Amadeus
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

# Initialisation du client Amadeus
amadeus = Client(
    client_id=AMADEUS_CLIENT_ID,
    client_secret=AMADEUS_CLIENT_SECRET,
    hostname='test'
)

def get_amadeus_token():
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_CLIENT_ID,
        "client_secret": AMADEUS_CLIENT_SECRET
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Erreur token Amadeus: {e}")
        return None

# -----------------------
# Dictionnaire de fallback
# -----------------------
    
_IATA_FALLBACK = {
    "tanger": "tangier",
    "barcelone": "barcelona",
    "lisbonne": "lisbon",
    "marrakech": "marrakech",
    "casablanca": "casablanca",
    "fes": "fez",
    "new york": "new york",
    "londres": "london",
    "rome": "rome",
    "paris": "paris",
    "milan": "milan",
    "madrid": "madrid",
    "bruxelles": "brussels",
    "amsterdam": "amsterdam",
    "berlin": "berlin",
    "munich": "munich",
    "vienne": "vienna",
    "prague": "prague",
    "budapest": "budapest",
    "varsovie": "warsaw",
    "moscou": "moscow",
    "istanbul": "istanbul",
    "dubaï": "dubai",
    "hong kong": "hong kong",
    "tokyo": "tokyo",
    "pekin": "beijing",
    "shanghai": "shanghai",
    "seoul": "seoul",
    "sydney": "sydney",
    "melbourne": "melbourne",
    "toronto": "toronto",
    "montreal": "montreal",
    "vancouver": "vancouver",
    "rio de janeiro": "rio de janeiro",
    "sao paulo": "sao paulo",
    "buenos aires": "buenos aires",
    "le cap": "cape town",
    "nairobi": "nairobi",
    "caire": "cairo",
    "dakar": "dakar",
    "tunis": "tunis",
    "alger": "algiers",
    "beyrouth": "beirut",
    "delhi": "delhi",
    "bombay": "mumbai",
    "bangalore": "bangalore",
    "chennai": "chennai",
    "kolkata": "kolkata",
    "singapour": "singapore",
    "kuala lumpur": "kuala lumpur",
    "bangkok": "bangkok",
    "jakarta": "jakarta",
    "manille": "manila",
    "athènes": "athens",
    "oslo": "oslo",
    "stockholm": "stockholm",
    "helsinki": "helsinki",
    "copenhague": "copenhagen",
    "dublin": "dublin",
    "edimbourg": "edinburgh",
    "glasgow": "glasgow",
    "manchester": "manchester",
    "birmingham": "birmingham",
    "nice": "nice",
    "lyon": "lyon",
    "toulouse": "toulouse",
    "marseille": "marseille",
    "geneve": "geneva",
    "zurich": "zurich",
    "francfort": "frankfurt",
    "hambourg": "hamburg",
    "cologne": "cologne",
    "venise": "venice",
    "florence": "florence",
    "naples": "naples",
    "bologne": "bologna",
    "porto": "porto",
    "valence": "valencia",
    "sevilla": "seville",
    "bilbao": "bilbao",
    "malaga": "malaga",
    "ibiza": "ibiza",
    "palma": "palma de mallorca",
    "las vegas": "las vegas",
    "los angeles": "los angeles",
    "san francisco": "san francisco",
    "chicago": "chicago",
    "miami": "miami",
    "washington": "washington",
    "boston": "boston",
    "philadelphie": "philadelphia",
    "atlanta": "atlanta",
    "dallas": "dallas",
    "houston": "houston",
    "detroit": "detroit",
    "phoenix": "phoenix",
    "seattle": "seattle",
    "montreal": "montreal",
    "calgary": "calgary",
    "ottawa": "ottawa",
    "quebec": "quebec city",
    "edmonton": "edmonton",
    "winnipeg": "winnipeg",
    "halifax": "halifax",
}  

# Dictionnaire global pour stocker les codes IATA en cache
_IATA_CACHE = {
    "tanger": "TNG",       # Tangier Ibn Battouta Airport :contentReference[oaicite:0]{index=0}
    "barcelone": "BCN",    # Barcelona-El Prat Airport :contentReference[oaicite:1]{index=1}
    "lisbonne": "LIS",     # Lisbon Humberto Delgado Airport :contentReference[oaicite:2]{index=2}
    "marrakech": "RAK",    # Marrakesh Menara Airport :contentReference[oaicite:3]{index=3}
    "casablanca": "CMN",   # Mohammed V International Airport :contentReference[oaicite:4]{index=4}
    "fes": "FEZ",          # Fès–Saïs Airport :contentReference[oaicite:5]{index=5}
    "new york": "JFK",     # John F. Kennedy International Airport
    "londres": "LHR",      # London Heathrow Airport
    "rome": "FCO",         # Leonardo da Vinci–Fiumicino Airport
    "paris": "CDG",        # Charles de Gaulle Airport :contentReference[oaicite:6]{index=6}
    "milan": "MXP",        # Milan Malpensa Airport
    "madrid": "MAD",       # Adolfo Suárez Madrid–Barajas Airport
    "bruxelles": "BRU",    # Brussels Airport
    "amsterdam": "AMS",    # Amsterdam Airport Schiphol
    "berlin": "BER",       # Berlin Brandenburg Airport
    "munich": "MUC",       # Munich Airport
    "vienne": "VIE",       # Vienna International Airport
    "prague": "PRG",       # Václav Havel Airport Prague
    "budapest": "BUD",     # Budapest Ferenc Liszt International Airport
    "varsovie": "WAW",     # Warsaw Chopin Airport
    "moscou": "SVO",       # Sheremetyevo International Airport
    "istanbul": "IST",     # Istanbul Airport
    "dubaï": "DXB",        # Dubai International Airport
    "hong kong": "HKG",    # Hong Kong International Airport
    "tokyo": "HND",        # Haneda Airport
    "pekin": "PEK",        # Beijing Capital International Airport
    "shanghai": "PVG",     # Shanghai Pudong International Airport
    "seoul": "ICN",        # Incheon International Airport
    "sydney": "SYD",       # Sydney Kingsford Smith Airport
    "melbourne": "MEL",    # Melbourne Airport
    "toronto": "YYZ",      # Toronto Pearson International Airport
    "montreal": "YUL",     # Montréal–Trudeau International Airport
    "vancouver": "YVR",    # Vancouver International Airport
    "rio de janeiro": "GIG", # Rio de Janeiro–Galeão International Airport
    "sao paulo": "GRU",    # São Paulo/Guarulhos–Governador André Franco Montoro International Airport
    "buenos aires": "EZE", # Ministro Pistarini International Airport
    "le cap": "CPT",       # Cape Town International Airport
    "nairobi": "NBO",      # Jomo Kenyatta International Airport
    "caire": "CAI",        # Cairo International Airport
    "dakar": "DSS",        # Blaise Diagne International Airport
    "tunis": "TUN",        # Tunis–Carthage International Airport
    "alger": "ALG",        # Houari Boumediene Airport
    "beyrouth": "BEY",     # Beirut–Rafic Hariri International Airport
    "delhi": "DEL",        # Indira Gandhi International Airport
    "bombay": "BOM",       # Chhatrapati Shivaji Maharaj International Airport
    "bangalore": "BLR",    # Kempegowda International Airport
    "chennai": "MAA",      # Chennai International Airport
    "kolkata": "CCU",      # Netaji Subhas Chandra Bose International Airport
    "singapour": "SIN",    # Singapore Changi Airport
    "kuala lumpur": "KUL", # Kuala Lumpur International Airport
    "bangkok": "BKK",      # Suvarnabhumi Airport
    "jakarta": "CGK",      # Soekarno–Hatta International Airport
    "manille": "MNL",      # Ninoy Aquino International Airport
    "athènes": "ATH",      # Athens International Airport
    "oslo": "OSL",         # Oslo Airport, Gardermoen
    "stockholm": "ARN",    # Stockholm Arlanda Airport
    "helsinki": "HEL",     # Helsinki Airport
    "copenhague": "CPH",   # Copenhagen Airport
    "dublin": "DUB",       # Dublin Airport
    "edimbourg": "EDI",    # Edinburgh Airport
    "glasgow": "GLA",      # Glasgow Airport
    "manchester": "MAN",   # Manchester Airport
    "birmingham": "BHX",   # Birmingham Airport
    "nice": "NCE",         # Nice Côte d'Azur Airport
    "lyon": "LYS",         # Lyon–Saint-Exupéry Airport
    "toulouse": "TLS",     # Toulouse–Blagnac Airport
    "marseille": "MRS",    # Marseille Provence Airport
    "geneve": "GVA",       # Geneva Airport
    "zurich": "ZRH",       # Zurich Airport
    "francfort": "FRA",    # Frankfurt Airport
    "hambourg": "HAM",     # Hamburg Airport
    "cologne": "CGN",      # Cologne Bonn Airport
    "venise": "VCE",       # Venice Marco Polo Airport
    "florence": "FLR",     # Florence Airport, Peretola
    "naples": "NAP",       # Naples International Airport
    "bologne": "BLQ",      # Bologna Guglielmo Marconi Airport
    "porto": "OPO",        # Francisco Sá Carneiro Airport
    "valence": "VLC",      # Valencia Airport
    "sevilla": "SVQ",      # Seville Airport
    "bilbao": "BIO",       # Bilbao Airport
    "malaga": "AGP",       # Málaga–Costa del Sol Airport
    "ibiza": "IBZ",        # Ibiza Airport
    "palma": "PMI",        # Palma de Mallorca Airport
    "las vegas": "LAS",    # Harry Reid International Airport
    "los angeles": "LAX",  # Los Angeles International Airport
    "san francisco": "SFO",# San Francisco International Airport
    "chicago": "ORD",      # O'Hare International Airport
    "miami": "MIA",        # Miami International Airport
    "washington": "IAD",   # Washington Dulles International Airport
    "boston": "BOS",       # Logan International Airport
    "philadelphie": "PHL", # Philadelphia International Airport
    "atlanta": "ATL",      # Hartsfield–Jackson Atlanta International Airport
    "dallas": "DFW",       # Dallas/Fort Worth International Airport
    "houston": "IAH",      # George Bush Intercontinental Airport
    "detroit": "DTW",      # Detroit Metropolitan Airport
    "phoenix": "PHX",      # Phoenix Sky Harbor International Airport
    "seattle": "SEA",      # Seattle–Tacoma International Airport
    "calgary": "YYC",      # Calgary International Airport
    "ottawa": "YOW",       # Ottawa Macdonald–Cartier International Airport
    "quebec": "YQB",       # Québec City Jean Lesage International Airport
    "edmonton": "YEG",     # Edmonton International Airport
    "winnipeg": "YWG",     # Winnipeg James Armstrong Richardson International Airport
    "halifax": "YHZ",      # Halifax Stanfield International Airport
}


# -----------------------
# Conversion ville → IATA
# -----------------------
def get_iata_code(city_name: str) -> Optional[str]:

    key = unidecode(city_name).lower()
    if key in _IATA_CACHE:
        return _IATA_CACHE[key]
    query = _IATA_FALLBACK.get(key, city_name)
    try:
        resp = amadeus.reference_data.locations.get(
            keyword=query,
            subType='AIRPORT',
            page={'limit': 3}
        )
        best = max(resp.data or [], key=lambda loc: loc.get("analytics", {})\
                                                .get("travelers", {}).get("score", 0),
                   default=None)
        if best:
            iata_code = best["iataCode"]
            _IATA_CACHE[key] = iata_code
            return iata_code
        return None
    except ResponseError as err:
        print(f"Erreur IATA pour {city_name}: {err}")
        return None

# -----------------------
# Fonction principale vols
# -----------------------
def search_flights(origin: str, destination: str, departure_date: str, adults: int = 1, children: int = 0, travel_class: str= "ECONOMY") -> dict:
    token = get_amadeus_token()
    if not token:
        return {"success": False, "error": "TOKEN_ERROR"}

    origin_iata = get_iata_code(origin)
    destination_iata = get_iata_code(destination)

    if not origin_iata or not destination_iata:
        return {
            "success": False,
            "error": "IATA_NOT_FOUND",
            "origin": origin_iata,
            "destination": destination_iata
        }

    try:
        print("🔍 Recherche de vols avec les paramètres :")
        print({
            "originLocationCode": origin_iata,
            "destinationLocationCode": destination_iata,
            "departureDate": departure_date,
            "travelClass": travel_class,
            "currencyCode": 'EUR',
            "adults": adults,
            "children": children,
            "max": 5
        })

        resp = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin_iata,
            destinationLocationCode=destination_iata,
            departureDate=departure_date,
            travelClass=travel_class,
            currencyCode='EUR',
            adults=adults,
            children=children,
            max=5
        )

        return {"success": True, "data": resp.data}

    except ResponseError as err:
        print("❌ Erreur Amadeus :", err.response.status_code)
        print("📩 Détail erreur :", err.response.body)
        return {"success": False, "error": err.response.body}

# -----------------------
# Analyse du texte libre
# -----------------------
def parse_flight_request(text: str) -> dict:
    text = text.lower()

    ville_match = re.search(r"de\s+(.+?)\s+à\s+(.+?)\s+(?:pour|le)", text)
    origin = ville_match.group(1).strip() if ville_match else None
    destination = ville_match.group(2).strip() if ville_match else None

    date_match = re.search(r"pour\s+le\s+(.+?)(?:\s+avec|\s+en|\s*$)", text)
    departure_date = None
    if date_match:
        parsed_date = dateparser.parse(date_match.group(1), languages=['fr'])
        if parsed_date:
            departure_date = parsed_date.strftime('%Y-%m-%d')

    adults_match = re.search(r"(\d+)\s+adulte", text)
    children_match = re.search(r"(\d+)\s+enfant", text)
    adults = int(adults_match.group(1)) if adults_match else 1
    children = int(children_match.group(1)) if children_match else 0

    travel_class = "ECONOMY"
    if "business" in text:
        travel_class = "BUSINESS"
    elif "premium" in text:
        travel_class = "PREMIUM_ECONOMY"
    elif "first" in text or "première" in text:
        travel_class = "FIRST"

    return {
        "origin": origin,
        "destination": destination,
        "departure_date": departure_date,
        "adults": adults,
        "children": children,
        "travel_class": travel_class
    }


