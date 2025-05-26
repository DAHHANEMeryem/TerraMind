from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
import os
import firebase_admin
from firebase_admin import credentials
from .services.ai_sql_database_public_service import check_stock_level
from .services.email_service import notify_make
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import json
from pathlib import Path
from config import Config
from sqlalchemy import text
from sqlalchemy import inspect


# Déclaration des outils
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()

ALERTED_FILE_PATH = Path("app/alerted_products.json")


def load_alerted_products():
    if ALERTED_FILE_PATH.exists():
        with open(ALERTED_FILE_PATH, "r") as file:
            content = file.read().strip()
            if not content:
                return set()
            return set(json.loads(content))
    return set()

def save_alerted_products(products_set):
    with open(ALERTED_FILE_PATH, "w") as file:
        json.dump(list(products_set), file)


def check_and_notify_stock():
    try:
        print("Vérification du stock en cours...")
        already_alerted_products = load_alerted_products()
        products_below_threshold = check_stock_level()

        # Liste actuelle de produits sous seuil
        current_understocked = {p["nom_produit"] for p in products_below_threshold}

        # 1️⃣ Identifier les nouveaux produits sous seuil
        new_alerts = []
        for product in products_below_threshold:
            name = product["nom_produit"]
            if name not in already_alerted_products:
                new_alerts.append(product)
                already_alerted_products.add(name)

        # 2️⃣ Envoyer les notifications si besoin
        if new_alerts:
            print(f"🟠 Nouveaux produits sous seuil : {new_alerts}")
            notify_make(new_alerts)

        # 3️⃣ Supprimer les produits qui ne sont PLUS sous seuil
        to_remove = already_alerted_products - current_understocked
        if to_remove:
            print(f"🟢 Produits revenus au stock normal : {to_remove}")
        already_alerted_products = already_alerted_products.intersection(current_understocked)

        # 4️⃣ Sauvegarder la liste mise à jour
        save_alerted_products(already_alerted_products)

    except Exception as e:
        print(f"❌ Erreur pendant la vérification du stock : {e}")


def create_app(config_class=Config): 
    app = Flask(__name__)
    CORS(app, origins=["http://localhost:4200"], supports_credentials=True,
         allow_headers=["Authorization", "Content-Type"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # Firebase
    cred = credentials.Certificate(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
    firebase_admin.initialize_app(cred)

    # Enregistrement des blueprints
    from app.routes.chat import chat_bp
    from app.routes.history import history_bp
    from app.routes.assistant import assistants_bp
    from app.routes.user import user_bp


    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(history_bp, url_prefix='/history')
    app.register_blueprint(assistants_bp, url_prefix='/assistant')
    app.register_blueprint(user_bp, url_prefix='/user')

    # Tâche planifiée
    scheduler = BackgroundScheduler()
    scheduler.start()

    print("🕒 Planificateur démarré, tâche ajoutée.")
    scheduler.add_job(
        func=check_and_notify_stock,
        trigger=IntervalTrigger(seconds=20),
        id='check_stock_job',
        name='Vérifier le stock automatiquement',
        replace_existing=True
    )

    with app.app_context():
        from app.models import user, search_history, assistant, execution, chat_session, role
        from app.models.assistant import Assistant
        from app.models.role import Role  

        # Test connexion
        try:
            db.session.execute(text('SELECT 1'))

        except Exception as e:
            print(f"⚠️ Impossible de se connecter à la base : {e}")
            return app

        # 👉 Vérifie si la table 'roles' existe avant insertion
        inspector = inspect(db.engine)
        if inspector.has_table(Role.__tablename__):

            roles_to_ensure = ['USER', 'ADMIN']
            for role_name in roles_to_ensure:
                existing_role = Role.query.filter_by(name=role_name).first()
                if not existing_role:
                    new_role = Role(name=role_name)
                    db.session.add(new_role)
                    print(f"✅ Rôle ajouté : {role_name}")
            db.session.commit()
        else:
            print("⚠️ Table 'roles' non trouvée, migration nécessaire avant insertion.")

        # 👉 Vérifie si la table 'assistants' existe avant insertion
        if inspector.has_table(Assistant.__tablename__):
            assistants_to_ensure = [
                {"domaine": "general", "name": "ChatBot"},
                {"domaine": "email", "name": "MailBot"},
                {"domaine": "booking", "name": "TourBot"},
                {"domaine": "data", "name": "VisionData"}
            ]
            for item in assistants_to_ensure:
                existing = Assistant.query.filter_by(name=item["name"]).first()
                if not existing:
                    new_assistant = Assistant(domaine=item["domaine"], name=item["name"])
                    db.session.add(new_assistant)
                    print(f"✅ Assistant ajouté : {item['name']}")
            db.session.commit()
        else:
            print("⚠️ Table 'assistants' non trouvée, migration nécessaire avant insertion.")

    return app
