from app.models.assistant import Assistant
from app.models.user import User
from flask import Blueprint, request, jsonify
from app import db
from firebase_admin import auth


assistants_bp = Blueprint('assistant', __name__)



@assistants_bp.route('', methods=['GET'])
def get_all_assistants():
    # 1. Récupérer le token depuis le header Authorization
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({"error": "Authorization token is required"}), 400

    # 2. Vérifier la validité du token
    try:
        decoded_token = auth.verify_id_token(token)
        # On peut extraire l'uid si nécessaire : uid = decoded_token.get('uid')
    except auth.InvalidIdTokenError:
        return jsonify({"error": "Invalid or expired token"}), 401
    except Exception as e:
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 401

    # 3. Si le token est valide, continuer avec la récupération des assistants
    try:
        assistants = Assistant.query.filter(Assistant.name != "ChatBot").all()

        assistants_data = [
            {
                "assistantId": a.assistantId,
                "name": a.name,
                "domaine": a.domaine,
                "isActive": a.isActive
            }
            for a in assistants
        ]

        return jsonify(assistants_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@assistants_bp.route('/<user_id>', methods=['PUT'])
def update_user_assistants(user_id):
    # 1. Récupérer le token depuis le header Authorization
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({"error": "Authorization token is required"}), 400

    # 2. Vérifier la validité du token
    try:
        decoded_token = auth.verify_id_token(token)
   
    except auth.InvalidIdTokenError:
        return jsonify({"error": "Invalid or expired token"}), 401
    except Exception as e:
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 401

    # 3. Récupérer les données JSON de la requête
    data = request.get_json()
    assistants_ids = data.get('assistants', [])

    # 4. Trouver l'utilisateur concerné
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404

    # 5. Récupérer les assistants associés
    assistants = Assistant.query.filter(Assistant.assistantId.in_(assistants_ids)).all()

    # 6. Mettre à jour la relation
    user.assistants = assistants

    try:
        db.session.commit()
        return jsonify({'message': 'Assistants mis à jour avec succès'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors de la mise à jour : {str(e)}'}), 500


@assistants_bp.route('/user/<user_id>', methods=['GET'])
def get_user_assistants(user_id):
    # Vérification du token (comme dans get_all_assistants)
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({"error": "Authorization token is required"}), 400
    try:
        decoded_token = auth.verify_id_token(token)
    except Exception as e:
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    # Récupérer la liste des assistants associés à cet utilisateur
    user_assistants_ids = [a.assistantId for a in user.assistants]

    return jsonify(user_assistants_ids), 200



@assistants_bp.route('/user', methods=['GET']) 
def get_assistants_for_current_user():
    token_header = request.headers.get('Authorization')
    if not token_header:
        return jsonify({"error": "Authorization token is required"}), 400

    token = token_header.replace('Bearer ', '').strip()

    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get('uid')
    except Exception as e:
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 401

    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    # Exemple: user.assistants contient des objets Assistant avec id et name
    assistants_data = []
    for assistant in user.assistants:
        assistants_data.append({
            "assistantId": assistant.assistantId,
            "name": assistant.name
        })

    return jsonify(assistants_data), 200

