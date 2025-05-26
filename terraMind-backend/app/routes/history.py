from flask import Blueprint, request, jsonify
from app import db
from app.models.chat_session import ChatSession
from firebase_admin import auth
from app.models.assistant import Assistant 
from app.models.user import User 
from app.models.search_history import SearchHistory 


history_bp = Blueprint('history', __name__)

@history_bp.route('/<string:assistant>', methods=['GET'])
def get_sessions_history(assistant):
    try:
        # Vérification de la présence du token d'autorisation
        token_header = request.headers.get('Authorization')
        if not token_header:
            return jsonify({"error": "Authorization token is required"}), 400
        
        # Extraction et vérification du token
        token = token_header.replace('Bearer ', '').strip()
        try:
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token.get('uid')
        except auth.InvalidIdTokenError:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Recherche de l'assistant
        assistant_obj = Assistant.query.filter_by(name=assistant).first()
        if not assistant_obj:
            return jsonify({"error": "Assistant not found"}), 404

        # Récupération triée des sessions (du plus récent au plus ancien)
        history = ChatSession.query \
            .filter_by(user_id=user_id, assistant_id=assistant_obj.assistantId) \
            .order_by(ChatSession.created_at.desc()) \
            .all()

        if not history:
            return jsonify({"message": "No sessions found for this assistant"}), 404

        # Retour des sessions sous forme de JSON
        return jsonify([
            {"title": session.title, "id": session.id}
            for session in history
        ]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@history_bp.route('/delete/<int:session_id>', methods=['DELETE', 'OPTIONS'])
def delete_specific_session(session_id):
    # Si c’est une requête OPTIONS (preflight), on renvoie juste OK
    if request.method == 'OPTIONS':
        return '', 200

    try:
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

        # Vérifier si la session existe et appartient à l'utilisateur
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()

        if not session:
            return jsonify({"error": "Chat session not found"}), 404

        # Supprimer la session
        db.session.delete(session)
        db.session.commit()

        return jsonify({"message": f"Chat session {session_id} deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@history_bp.route('/update/<int:session_id>', methods=['PUT'])
def update_title_session(session_id):
    try:
        # Vérifie que l'en-tête Authorization est présent
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

        # Vérifie que la session existe et appartient à l'utilisateur
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        if not session:
            return jsonify({"error": "Chat session not found"}), 404

        # Récupère la nouvelle valeur du titre depuis le corps de la requête
        data = request.get_json()
        new_title = data.get('title')
        if not new_title:
            return jsonify({"error": "New title is required"}), 400

        # Met à jour le titre de la session
        session.title = new_title
        db.session.commit()

        return jsonify({"message": f"Chat session {session_id} updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@history_bp.route('/', methods=['GET'])
def get_all_chat_sessions():
    token_header = request.headers.get('Authorization')
    if not token_header:
        return jsonify({"error": "Authorization token is required"}), 400

    token = token_header.replace('Bearer ', '').strip()
    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get('uid')
    except Exception as e:
        return jsonify({"error": "Invalid or expired token", "details": str(e)}), 401

    # Ici, on récupère toutes les sessions sans filtrer sur un assistant particulier
    results = (
        db.session.query(
            ChatSession.id,
            ChatSession.title,
            ChatSession.created_at,
            User.id.label('user_id'),
            User.nom.label('user_name'),
            Assistant.assistantId,
            Assistant.name.label('assistant_name')
        )
        .join(User, ChatSession.user_id == User.id)
        .join(Assistant, ChatSession.assistant_id == Assistant.assistantId)
        .all()
    )

    sessions = []
    for row in results:
        sessions.append({
            'session_id': row.id,
            'title': row.title,
            'created_at': row.created_at,
            'user_id': row.user_id,
            'user_name': row.user_name,
            'assistant_id': row.assistantId,
            'assistant_name': row.assistant_name,
        })
    return jsonify(sessions)


@history_bp.route('/details', methods=['GET'])
def chat_details():
    # Vérification du token dans l’en-tête Authorization
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({"error": "Authorization token is required"}), 400

    try:
        decoded_token = auth.verify_id_token(token)
        # Token valide, on continue
    except auth.InvalidIdTokenError:
        return jsonify({"error": "Invalid or expired token"}), 401
    except Exception as e:
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 401

    user_id = request.args.get('user_id')
    session_id = request.args.get('session_id')

    if not user_id or not session_id:
        return jsonify({'error': 'user_id et session_id sont requis'}), 400

    try:
        messages = db.session.query(SearchHistory).filter_by(user_id=user_id, chat_id=session_id)\
                                                  .order_by(SearchHistory.created_at.asc())\
                                                  .all()

        if not messages:
            return jsonify({'message': 'Aucun message trouvé pour cette session'}), 404

        result = [{
            'id': msg.id,
            'query': msg.query,
            'result': msg.result,
            'created_at': msg.created_at.isoformat()
        } for msg in messages]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500