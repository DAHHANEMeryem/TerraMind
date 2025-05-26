import json
import openai
import os
from dotenv import load_dotenv

load_dotenv()

# Set up the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")


def analyze_intent(message):
    """
    Analyze user message to determine intent (send email, get weather, query database, book_flight, book_hotel , or chat)
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """You are an assistant that analyzes user messages to determine if they contain a request to:
1. Send an email (action: "send_email")
2. Get weather information (action: "get_weather")
3. Query business database (action: "query_database")
4. Book a flight (action: "book_flight")
5. Book a hotel (action: "book_hotel")
6. Just a regular chat message (action: "chat")

For emails, extract "to", "subject", and "body" if present.
For weather, extract "location" if present.
For database, extract "question" in natural language form.
For flight, extract: 
    - "origin": departure city or IATA code
    - "destination": arrival city or IATA code
    - "date": ISO format (YYYY-MM-DD)
    - "travel_class": ECONOMY | PREMIUM_ECONOMY | BUSINESS | FIRST (if mentioned, default to ECONOMY otherwise)
For hotel, extract:
    - "destination": city name
    - "check_in": ISO format (YYYY-MM-DD)
    - "check_out": ISO format (YYYY-MM-DD)
    - "adults": number of adults
    - "rooms": number of rooms

Respond in JSON format with the following structure:
{
  "action": "send_email" | "get_weather" | "query_database" | "book_flight" | "book_hotel" | "chat",
  "data": {
    // For email
    "to": "recipient email",
    "subject": "email subject",
    "body": "email content"

    // FOR for weather
    "location": "city name",

    // FOR query databse
    "question": "text of user request"

    // For flight
    "origin": "Madrid",
    "destination": "Paris",
    "date": "2025-06-23",
    "travel_class": "BUSINESS"

    // For hotel
    "destination": "Paris",
    "check_in": "2025-06-01",
    "check_out": "2025-06-07",
    "adults": 2,
    "rooms": 1
  },
  "confidence": 0.0-1.0 // How confident you are in this classification
}

Only extract information that is clearly stated or can be reasonably inferred."""
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in intent analysis: {e}")
        return {"action": "chat", "confidence": 0, "data": {}}


def generate_chat_response(message, history=None):
    """
    Génère une réponse avec prise en compte de l'historique (limité aux 15 derniers échanges max)
    """
    if history is None:
        history = []

    try:
        MAX_TURNS = 15  # Limite à 15 derniers échanges (30 messages max)

        # Tronquer l’historique si besoin (on garde les 2 * MAX_TURNS derniers messages)
        truncated_history = history[-2 * MAX_TURNS:]

        # Ajout du message utilisateur actuel
        messages = truncated_history + [{"role": "user", "content": message}]

        # Prompt système légèrement enrichi
        system_prompt = {
            "role": "system",
            "content": (
                "Tu es un assistant utile, amical et compétent qui fournit des réponses claires et précises."
            )
        }

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[system_prompt] + messages
        ) 

        return response.choices[0].message.content

    except Exception as e:
        print(f"Erreur génération réponse: {e}")
        print(f"Contenu envoyé à OpenAI (dernier historique tronqué) : {messages}")
        return "Désolé, je rencontre un problème pour répondre."


def analyser_message(message):
    """
    Analyse un message utilisateur pour détecter une intention liée à la base de données
    (ex: get_produits_rupture_ville) et extraire les paramètres nécessaires.
    Retourne un dictionnaire avec "intent" et "params".
    """
    try:
        response = openai.chat.completions.create(

            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """Tu es un assistant intelligent qui interprète les messages utilisateurs pour exécuter des requêtes sur une base de données MySQL liée à la gestion des ventes.

Exemples d’intentions possibles :

- get_clients_par_annee
- get_nouveaux_clients_par_mois
- get_clients_plus_fidelite
- get_clients_plus_achats
- get_clients_ayant_recu_recompenses
- get_nombre_retours_par_client
- get_produits_retournes_par_client
- get_clients_inscrits_apres
- get_clients_par_genre
- get_age_clients
- get_ventes_par_ville
- get_clients_avec_achats_superieurs

- get_top_10_produits_vendus
- get_produits_plus_retournes
- get_produits_rupture_stock
- get_produits_sous_seuil_alerte
- get_produits_par_fournisseur
- get_produits_plus_grand_montant_rembourse
- get_produits_plus_stockes_par_magasin
- get_produits_jamais_vendus
- get_top_3_categories_produits_vendus
- get_produits_ajoutes_apres
- get_nombre_produits_par_categorie
- get_produit_plus_cher
- get_produit_moins_cher
- get_produits_les_plus_vendus

- get_chiffre_affaires_total
- get_chiffre_affaires_par_mois
- get_ventes_par_magasin
- get_montant_moyen_vente_par_magasin
- get_magasins_plus_faible_ca
- get_nb_ventes_par_canal
- get_ventes_par_jour_semaine
- get_evolution_ventes_par_mois

- get_employes_plus_ventes
- get_salaire_moyen_par_role
- get_employes_par_magasin
- get_employes_par_role
- get_nombre_employes_par_magasin
- get_ventes_par_employe
- get_chiffre_affaire_par_employe
- get_employes_ventes_apres

- get_fournisseur_plus_stock

- get_repartition_par_paiement,
- get_all_methodes_paiement,
- count_ventes_par_methode,
- sum_ventes_par_methode,
- paiements_par_jour,
- paiements_par_mois,
- get_ventes_par_methode,
- get_ventes_superieures_a,

- get_pourcentage_retours,
- get_retours_par_statut,
- get_raisons_retour_frequentes,
- get_nombre_retours_par_produit,
- get_retours_par_statut,

Tu dois répondre strictement au format JSON suivant :

{
  "intent": "nom_de_l_intention",
  "params": {
    "param1": "valeur",
    "param2": "valeur"
  }
}

Exemple :

Message : "Quels sont les produits en rupture de stock à Casablanca ?"
Réponse attendue :

{
  "intent": "get_produits_rupture_ville",
  "params": {
    "ville": "Casablanca"
  }
}

Ne réponds que par un objet JSON valide.
"""
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        content = response.choices[0].message.content.strip()
        return json.loads(content)

    except Exception as e:
        print(f"[ERREUR] Analyse d’intention : {e}")
        return {"intent": "unknown", "params": {}}

