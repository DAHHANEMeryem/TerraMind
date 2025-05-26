from flask import Blueprint, request, jsonify
from firebase_admin import auth
from firebase_admin import firestore
from app import db
from app.models.user import User
from app.models.role import Role
from google.cloud import firestore  

from google.cloud import firestore

firestore_client = firestore.Client()

user_bp = Blueprint('user', __name__)

@user_bp.route('/', methods=['GET'])
def get_all_users():
    try:
        # Token
        token_header = request.headers.get('Authorization')
        if not token_header:
            return jsonify({"error": "Authorization token is required"}), 400
        token = token_header.replace('Bearer ', '').strip()

        # Vérification du token
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get('uid')

        # Vérification de l'utilisateur
        current_user = db.session.query(User).filter_by(id=user_id).first()
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        # Récupération des utilisateurs
        users = User.query.all()
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "nom": user.nom,
                "nom_utilisateur": user.nom_utilisateur,
                "email": user.email,
                "role": user.role.name if user.role else None,
                "is_blocked":user.is_blocked
            })

        return jsonify(user_list), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500



@user_bp.route('/add_user', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        print("Données reçues:", data)

        user_id = data.get('id')
        nom = data.get('nom')
        nom_utilisateur = data.get('nom_utilisateur')
        email = data.get('email')
        role_name = data.get('role', 'User')

        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(id=user_id).first()
        if existing_user:
            return jsonify({"message": "Utilisateur déjà existant", "user": existing_user.id}), 200

        # Trouver ou créer le rôle
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name)
            db.session.add(role)
            db.session.commit()

        new_user = User(
            id=user_id,
            nom=nom,
            nom_utilisateur=nom_utilisateur,
            email=email,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "Utilisateur ajouté avec succès", "user": new_user.id}), 200

    except Exception as e:
        print(f"Erreur: {e}")
        db.session.rollback()
        return jsonify({"message": "Erreur interne du serveur"}), 500





@user_bp.route('/update_user/<user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        token_header = request.headers.get('Authorization')
        if not token_header:
            return jsonify({"error": "Authorization token is required"}), 400

        token = token_header.replace('Bearer ', '').strip()

        try:
            decoded_token = auth.verify_id_token(token)
            token_user_id = decoded_token.get('uid')
        except Exception as e:
            return jsonify({"error": f"Token verification failed: {str(e)}"}), 401

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404

        data = request.get_json()
        nom = data.get('nom')
        nom_utilisateur = data.get('nom_utilisateur')
        email = data.get('email')
        role_name = data.get('role')

        # Vérifier que le nom_utilisateur est unique sauf pour cet utilisateur
        user_with_same_username = User.query.filter(User.nom_utilisateur == nom_utilisateur, User.id != user_id).first()
        if user_with_same_username:
            return jsonify({"message": "Ce nom d'utilisateur est déjà utilisé"}), 400

        # Mettre à jour les champs
        user.nom = nom
        user.nom_utilisateur = nom_utilisateur
        user.email = email

        # Trouver le rôle
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({"message": "Rôle invalide"}), 400

        user.role = role

        db.session.commit()

        return jsonify({"message": "Utilisateur mis à jour avec succès", "user": user.id, "email": user.email}), 200

    except Exception as e:
        print(f"Erreur: {e}")
        db.session.rollback()
        return jsonify({"message": "Erreur interne du serveur"}), 500






@user_bp.route('/delete-user/<string:user_id>/<string:username>', methods=['DELETE'])
def delete_user(user_id, username):
    try:
        token_header = request.headers.get('Authorization')
        if not token_header:
            return jsonify({"error": "Token d'authentification requis"}), 401

        token = token_header.replace('Bearer ', '').strip()
        decoded_token = auth.verify_id_token(token)
        current_user_id = decoded_token.get('uid')

        current_user = User.query.filter_by(id=current_user_id).first()
        if not current_user:
            return jsonify({"error": "Utilisateur connecté introuvable"}), 404



        # VERIFICATION : empêcher suppression de soi-même
        if user_id == current_user_id:
            return jsonify({"error": "Vous ne pouvez pas supprimer votre propre compte."}), 403

        # Supprimer dans Firebase Auth
        auth.delete_user(user_id)

        # Supprimer dans Firestore
        firestore_client.collection("users").document(user_id).delete()
        firestore_client.collection("usernames").document(username).delete()

        # Supprimer dans MySQL
        user_to_delete = User.query.filter_by(id=user_id).first()
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()

        return jsonify({"message": "Utilisateur supprimé avec succès"}), 200

    except Exception as e:
        print("Erreur interne:", e)
        return jsonify({"error": "Erreur : " + str(e)}), 500


@user_bp.route('/toggle_block_user/<user_id>', methods=['PUT'])
def toggle_block_user(user_id):
    try:
        token_header = request.headers.get('Authorization')
        if not token_header:
            return jsonify({"error": "Authorization token is required"}), 400

        token = token_header.replace('Bearer ', '').strip()
        decoded_token = auth.verify_id_token(token)
        admin_user_id = decoded_token.get('uid')

        # Récupérer l'utilisateur dans MySQL
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Utilisateur introuvable"}), 404

        # Inverser le statut de blocage
        user.is_blocked = not user.is_blocked
        db.session.commit()

        # Mettre à jour dans Firestore
        user_doc_ref = firestore_client.collection('users').document(user_id)
        user_doc_ref.update({
            'is_blocked': user.is_blocked
        })

        return jsonify({
            "message": f"Utilisateur {'bloqué' if user.is_blocked else 'débloqué'} avec succès",
            "is_blocked": user.is_blocked
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@user_bp.route('/roles', methods=['GET'])
def list_roles():
    # Vérification du token
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({"error": "Authorization token is required"}), 400

    try:
        decoded_token = auth.verify_id_token(token)
        # Si besoin : uid = decoded_token.get('uid')
    except auth.InvalidIdTokenError:
        return jsonify({"error": "Invalid or expired token"}), 401
    except Exception as e:
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 401

    # Si le token est valide, continuer
    roles = Role.query.all()
    return jsonify([{"id": role.id, "name": role.name} for role in roles]), 200




