from flask import request, jsonify, Blueprint
from firebase_admin import auth
from datetime import datetime
from app import db
from app.services.openai_service import analyze_intent, generate_chat_response ,analyser_message
from app.services.ai_sql_database_private_service import intent_function_map
from app.services.email_service import send_email
from app.services.weather_service import get_weather
from app.services.ai_sql_database_public_service import query_database_with_gpt
from app.models.search_history import SearchHistory
from app.models.chat_session import ChatSession
from app.models.user import User
from app.models.assistant import Assistant
from app.services.flight_service import search_flights, get_iata_code
from app.services.hotels_service import search_hotels


chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/', methods=['POST'])
def chat():
    try:
        # Récupération des données JSON de la requête
        data = request.get_json()
        assistant_name = data.get("assistant")
        user_message = data.get('message')
        chat_id = data.get('chat_id')
        token_header = request.headers.get('Authorization')

        # Validation des champs obligatoires
        if not token_header:
            return jsonify({"error": "Authorization token is required"}), 400
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        if not chat_id:
            return jsonify({"error": "Chat ID is required"}), 400

        # Extraction et vérification du token Firebase
        token = token_header.replace('Bearer ', '').strip()
        try:
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token.get('uid')
        except Exception:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Vérification de l'existence de la session de chat
        chat_session = ChatSession.query.filter_by(id=chat_id).first()
        if not chat_session:
            return jsonify({"error": "Invalid Chat ID"}), 400

        print(f"User ID extracted from token: {user_id}")

        # Récupération de l'historique du chat (fonction externe)
        chat_history = get_openai_chat_history(chat_id, user_id)

        # Analyse d'intention via OpenAI
        print("Analyzing intent...")
        analysis = analyze_intent(user_message)
        print(f"Intent analysis: {analysis}")

        action = analysis.get("action")
        confidence = analysis.get("confidence", 0)
        intent_data = analysis.get("data", {})
        ai_response = ""

        # Actions autorisées par assistant
        authorized_actions = {
            "VisionData": ["query_database"],
            "TourBot": ["book_flight", "book_hotel"],
            "MailBot": ["send_email"],
            "WeatherBot": ["get_weather"],
            "chatBot": ["chat"]
        }
        allowed = authorized_actions.get(assistant_name, [])

        # Vérifier si l'action est autorisée
        if action not in allowed:
            ai_response = "Désolé, cet assistant ne gère pas cette action."

            # Enregistrer l'historique même pour actions non autorisées
            user = User.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({"error": "User not found"}), 404

            new_history = SearchHistory(
                user_id=user_id,
                chat_id=chat_id,
                query=user_message,
                result=ai_response,
                created_at=datetime.utcnow()
            )
            db.session.add(new_history)
            db.session.commit()

            return jsonify({"message": ai_response})

        # Gestion des actions
        if action == 'send_email' and confidence > 0.7 and intent_data.get('to'):
            print("Sending email...")
            action_response = send_email(
                intent_data.get('to'),
                intent_data.get('subject', 'No Subject'),
                intent_data.get('body', 'No Content')
            )
            ai_response = (
                f"Email sent to {intent_data.get('to')} with subject \"{intent_data.get('subject', 'No Subject')}\"."
                if action_response.get('success')
                else f"Failed to send email: {action_response.get('error', 'Unknown error')}"
            )

        elif action == 'get_weather' and confidence > 0.7 and intent_data.get('location'):
            print("Getting weather...")
            action_response = get_weather(intent_data['location'])
            ai_response = (
                action_response.get('message')
                if action_response.get('success')
                else f"Failed to get weather for {intent_data.get('location')}: {action_response.get('error', 'Unknown error')}"
            )

        elif action == 'query_database' and confidence > 0.7 and intent_data.get('question'):
            print("Analyse de la question utilisateur pour déterminer l'intention...")
            question = intent_data['question']
            print(f"Question posée pour la base de données : {question}")

            # Analyse GPT pour intent + params
            result_intent = analyser_message(question)
            intent = result_intent.get("intent")
            params = result_intent.get("params", {})

            print(f"Intention détectée : {intent}")
            print(f"Paramètres extraits : {params}")

            if intent in intent_function_map:
                try:
                    # Appel dynamique de la fonction liée à l'intention
                    db_response = intent_function_map[intent](**params)

                    if not db_response:
                        ai_response = "Désolé, aucun résultat trouvé pour votre demande."
                    else:
                        intro_prompt = f"Rédige une phrase naturelle pour introduire une liste de résultats correspondant à cette question : \"{question}\""
                        intro_response = generate_chat_response(intro_prompt)
                        intro_phrase = intro_response if isinstance(intro_response, str) else intro_response.get("message", "Voici les résultats :")

                        columns = list(db_response[0].keys())
                        table = '<table id="result-table" class="styled-table" cellpadding="5" cellspacing="0"><thead><tr>'
                        for col in columns:
                            table += f'<th>{col}</th>'
                        table += '</tr></thead><tbody>'
                        for row in db_response:
                            table += '<tr>'
                            for col in columns:
                                table += f'<td>{row[col]}</td>'
                            table += '</tr>'
                        table += '</tbody></table>'

                        ai_response = intro_phrase + "<br><br>" + table
                except Exception as e:
                    print(f"Erreur lors de l'appel à la fonction {intent} : {e}")
                    ai_response = f"Une erreur est survenue lors de l'exécution de la requête : {e}"
            else:
                ai_response = f"Désolé, je n'ai pas compris."


        elif action == 'book_flight' and confidence > 0.7:
            origin = intent_data.get("origin")
            destination = intent_data.get("destination")
            date = intent_data.get("date")
            adults = intent_data.get("adults", 1)
            children = intent_data.get("children", 0)
            travel_class = intent_data.get("travel_class", "ECONOMY")

            if origin and destination and date:
                origin_iata = get_iata_code(origin)
                destination_iata = get_iata_code(destination)

                if not origin_iata or not destination_iata:
                    return jsonify({"response": "Désolé, je n’ai pas pu identifier les codes des villes."})

                flights_result = search_flights(origin, destination, date, adults=adults, children=children, travel_class=travel_class)

                if flights_result and "data" in flights_result:
                    flight_messages = []
                    for idx, offer in enumerate(flights_result["data"], 1):
                        msg = f"<b>✈️ Offre #{idx}</b><br>"
                        total_price = offer['price']['total']
                        currency = offer['price']['currency']
                        msg += f"Prix total : {total_price} {currency}<br>"

                        pricing_info = offer.get('travelerPricings', [])[0]
                        fare_details = pricing_info.get('fareDetailsBySegment', [])
                        classes = [fd.get('cabin', 'N/A') for fd in fare_details]
                        msg += f"Classe de voyage : {', '.join(set(classes))}<br>"

                        for itin_idx, itinerary in enumerate(offer['itineraries']):
                            msg += f"🔁 Itinéraire #{itin_idx + 1} — {len(itinerary['segments'])} segment(s)<br>"
                            for seg in itinerary['segments']:
                                dep = seg['departure']
                                arr = seg['arrival']
                                carrier = seg['carrierCode']
                                flight_number = seg['number']
                                dep_time = dep['at'][11:16]
                                arr_time = arr['at'][11:16]
                                msg += f"{carrier}{flight_number} : {dep['iataCode']} → {arr['iataCode']} ({dep_time} → {arr_time})<br>"
                        flight_messages.append(msg)

                    ai_response = "<p>Voici quelques offres de vol :</p><br>" + "".join(flight_messages)
                else:
                    ai_response = "Désolé, une erreur est survenue lors de la recherche de vols."
            else:
                ai_response = "Merci de préciser l'origine, la destination et la date du vol."

        elif action == 'book_hotel' and confidence > 0.7:
            try:
                destination = intent_data.get('destination', '').strip()
                check_in = intent_data.get('check_in', '').strip()
                check_out = intent_data.get('check_out', '').strip()

                if not all([destination, check_in, check_out]):
                    return jsonify({"message": "Merci de préciser la destination et les dates"})

                hotel_result = search_hotels(
                    destination=destination,
                    check_in=check_in,
                    check_out=check_out,
                    adults=int(intent_data.get('adults', 1)),
                    rooms=int(intent_data.get('rooms', 1))
                )

                if not hotel_result.get("success"):
                    return jsonify({"message": hotel_result["error"]})

                results = []
                message_lines = []
                count = len(hotel_result["data"])
                hotel_word = "hôtel" if count == 1 else "hôtels"
                plural_suffix = '' if count == 1 else 's'
                check_in_fmt = format_date_french(check_in)
                check_out_fmt = format_date_french(check_out)

                for idx, hotel in enumerate(hotel_result["data"], start=1):
                    hotel_info = hotel["hotel"]
                    offer = hotel["offers"][0]
                    address = hotel_info.get("address", {}).get("lines", ["Adresse non disponible"])[0]
                    price_info = offer.get("price", {})
                    currency = price_info.get("currency", '')
                    try:
                        total_price = float(price_info.get("total", 0))
                        price_formatted = f"{total_price:,.2f}".replace(",", " ").replace(".", ",") + f" {currency}"
                    except:
                        price_formatted = f"{price_info.get('total', '?')} {currency}"

                    hotel_line = (
                        f"🏨 Offre #{idx}</br>"
                        f"Nom : {hotel_info.get('name', 'Nom inconnu')}</br>"
                        f"Adresse : {address}</br>"
                        f"📅 Dates : {check_in_fmt} → {check_out_fmt}</br>"
                        f"💰 Prix total : {price_formatted}</br><br>"
                    )
                    message_lines.append(hotel_line)

                ai_response = (
                    f"Voici {count} {hotel_word}{plural_suffix} disponibles du {check_in_fmt} au {check_out_fmt} :<br><br>"
                    + "".join(message_lines)
                )
            except Exception as e:
                print(f"Erreur lors de la recherche d'hôtels : {e}")
                ai_response = "Une erreur est survenue lors de la recherche d'hôtels."

        elif action == 'chat' and confidence > 0.7:
            print("ChatBot processing message...")
            ai_response = generate_chat_response(user_message)

        else:
            # Action non gérée ou confiance insuffisante
            ai_response = "Je n'ai pas compris votre demande, pourriez-vous reformuler ?"

        # Enregistrement de la recherche dans l'historique
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        history = SearchHistory(
            user_id=user_id,
            chat_id=chat_id,
            query=user_message,
            result=ai_response,
            created_at=datetime.utcnow()
        )
        db.session.add(history)
        db.session.commit()

        return jsonify({"message": ai_response})

    except Exception as e:
        print(f"Erreur inattendue dans la route chat: {e}")
        return jsonify({"error": "Une erreur interne est survenue."}), 500


@chat_bp.route('/new_chat', methods=['POST'])
def create_chat():
    try:
        # Décodage du token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({"error": "Authorization token is required"}), 400
        
        try:
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token.get('uid')
            if not user_id:
                return jsonify({"error": "User ID not found in token"}), 400
        except auth.InvalidIdTokenError:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Récupération du message du frontend pour le titre du chat
        data = request.get_json()
        first_message = data.get('first_message', '')
        
        if not first_message:
            return jsonify({"error": "First message is required"}), 400

        # Assurez-vous que le nom de l'assistant est valide
        assistant_name = data.get('assistant')  
        if not assistant_name:
            return jsonify({"error": "Assistant name is required"}), 400

        # Récupération de l'assistant correspondant au nom fourni
        assistant = Assistant.query.filter_by(name=assistant_name).first()
        if not assistant:
            return jsonify({"error": "Assistant not found"}), 404

        # Création du chat
        new_chat = ChatSession(user_id=user_id, title=first_message, assistant_id=assistant.assistantId)
        db.session.add(new_chat)
        db.session.commit()

        return jsonify({
            "chat_id": new_chat.id,
            "title": new_chat.title,
            "assistant_id": new_chat.assistant_id,
            "created_at": new_chat.created_at.isoformat()
        }), 201  # Ajout du code de statut 201 pour une création réussie

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Could not create chat: {str(e)}"}), 500


@chat_bp.route('/<int:chat_id>', methods=['GET'])
def get_chat_history(chat_id):
    # Vérification de l'existence du token d'autorisation
    token_header = request.headers.get('Authorization')
    if not token_header:
        return jsonify({"error": "Authorization token is required"}), 400

    # Extraction du token
    token = token_header.replace('Bearer ', '').strip()

    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get('uid')
    except auth.InvalidIdTokenError:
        return jsonify({"error": "Invalid or expired token"}), 401

    # Vérification si l'utilisateur existe
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Récupération des paramètres de pagination
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 5, type=int)

    # Calcul des messages paginés
    messages = (
        db.session.query(SearchHistory)
        .filter_by(chat_id=chat_id, user_id=user_id)
        .order_by(SearchHistory.created_at.asc())
        .offset((page - 1) * page_size)  # Déplace le curseur selon la page
        .limit(page_size)  # Limite le nombre de messages récupérés
        .all()
    )

    # Structurer les messages dans le format attendu par le frontend
    messages_list = []
    for msg in messages:
        messages_list.append({'text': msg.query, 'isUser': True})   # Message utilisateur
        messages_list.append({'text': msg.result, 'isUser': False}) # Message bot

    return jsonify(messages_list), 200


def get_openai_chat_history(chat_id, user_id):
    """
    Récupère l'historique du chat et le formate pour OpenAI (role/user/assistant)
    """
    history = (
        db.session.query(SearchHistory)
        .filter_by(chat_id=chat_id, user_id=user_id)
        .order_by(SearchHistory.created_at.asc())
        .all()
    )

    messages = []
    for entry in history:
        messages.append({"role": "user", "content": entry.query})
        messages.append({"role": "assistant", "content": entry.result})

    return messages


def format_date_french(date_str):
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                return date_obj.strftime("%A %d %B %Y").capitalize()
            except:
                return date_str
