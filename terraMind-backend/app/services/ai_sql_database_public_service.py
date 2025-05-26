from sqlalchemy import create_engine, text, inspect
import openai
from decimal import Decimal
import json
import os

DATABASE_URL = "mysql+mysqlconnector://root:meriem@localhost/analyse_ventes_db"
FAQ_FILE = "faq_queries.json"
MAX_TURNS = 15
engine = create_engine(DATABASE_URL)



def load_faq_queries():
    """Charge les requêtes FAQ depuis un fichier JSON local."""
    if os.path.exists(FAQ_FILE):
        with open(FAQ_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_schema_and_format(engine):
    """Récupère le schéma des tables, les relations et génère une représentation textuelle du schéma."""
    inspector = inspect(engine)
    schema_str = ""
    
    # Schéma des tables
    schema = {}
    relationships = []

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        schema[table_name] = [col['name'] for col in columns]

        # Ajout du schéma sous forme de chaîne de caractères
        schema_str += f"- {table_name}({', '.join([col['name'] for col in columns])})\n"

        # Relations
        foreign_keys = inspector.get_foreign_keys(table_name)
        for fk in foreign_keys:
            relationships.append({
                "from_table": table_name,
                "from_column": fk['constrained_columns'][0],
                "to_table": fk['referred_table'],
                "to_column": fk['referred_columns'][0]
            })

    # Ajout des relations sous forme de chaîne de caractères
    if relationships:
        schema_str += "\nRelations:\n"
        for r in relationships:
            schema_str += f"- {r['from_table']}.{r['from_column']} = {r['to_table']}.{r['to_column']}\n"

    return schema_str

def query_database_with_gpt(question, history=None):
    """
    Prend une question utilisateur, génère une requête SQL via GPT,
    l'exécute et retourne les résultats.
    """
    if history is None:
        history = []

    try:
        # Limite l'historique envoyé à GPT
        truncated_history = history[-2 * MAX_TURNS:]

        # Récupération et formatage du schéma
        full_schema_str = get_schema_and_format(engine)

        # Chargement des requêtes fréquentes
        faq_queries = load_faq_queries()

        faq_str = "\n".join([f"Question: {q}\nRequête SQL: {sql}" for q, sql in faq_queries.items()])

        # Création du prompt système
        system_prompt = {
           "role": "system",
           "content": (
           "Tu es un assistant SQL. Tu dois générer des requêtes MySQL **EXACTES** et sans erreur, "
           "en respectant la structure de la base de données et les relations entre les tables.\n\n"
           "Voici le schéma **complet** de la base de données :\n"
           f"{full_schema_str}\n\n"
           "Voici des exemples de requêtes fréquentes :\n"
           f"{faq_str}\n\n"
           "Si une question est ambiguë, réponds en demandant plus de précisions avant de générer une requête SQL.\n"
           "Génère uniquement la requête SQL, sans explication, et assure-toi qu'elle fonctionne pour la base de données MySQL."
    )
}
        # Construction du message complet
        messages = [system_prompt] + truncated_history + [{"role": "user", "content": question}]

        # Appel à l’API OpenAI
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        sql_query = response.choices[0].message.content.strip()

        # Nettoyage si GPT renvoie avec des balises ```sql
        if '```sql' in sql_query:
            sql_query = sql_query.split('```sql')[-1].split('```')[0].strip()

        # Exécution SQL
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()

        # Formatage des résultats
        formatted = []
        for row in rows:
            formatted_row = {}
            for col, val in zip(columns, row):
                formatted_row[col] = float(val) if isinstance(val, Decimal) else val
            formatted.append(formatted_row)

        return {"success": True, "query": sql_query, "results": formatted}

    except Exception as e:
        return {"success": False, "error": str(e)}

def check_stock_level():
    # Requête SQL pour obtenir les produits sous leur seuil d'alerte
    query = """
    SELECT p.nom_produit, s.quantite_stock, s.seuil_alerte
    FROM produits p
    JOIN stocks  s ON p.id_produit = s.id_produit
    WHERE s.quantite_stock <= s.seuil_alerte
    """
    with engine.connect() as connection:
        result = connection.execute(text(query))
        products = result.fetchall()

    # Retourner une liste de produits sous le seuil d'alerte
    return [{"nom_produit": product[0], "quantite_stock": product[1], "seuil_alerte": product[2]} for product in products]



