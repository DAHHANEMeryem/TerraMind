from sqlalchemy import create_engine, text

# Configuration SQLAlchemy
DATABASE_URL = "mysql+mysqlconnector://root:meriem@localhost/analyse_ventes_db"
engine = create_engine(DATABASE_URL)

#Fonctions liées aux clients
def get_clients_par_annee(annee):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT nom_client, prenom, email, date_inscription 
            FROM clients 
            WHERE YEAR(date_inscription) = :annee
        """), {"annee": annee})
        return [dict(row._mapping) for row in result]
def get_nouveaux_clients_par_mois():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DATE_FORMAT(date_inscription, '%Y-%m') AS mois, COUNT(*) AS nouveaux_clients
            FROM clients
            GROUP BY mois
            ORDER BY mois
        """))
        return [dict(row._mapping) for row in result]
def get_clients_plus_fidelite():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT nom_client, prenom, points_fidelite
            FROM clients
            ORDER BY points_fidelite DESC
            LIMIT 10
        """))
        return [dict(row._mapping) for row in result]
def get_clients_plus_achats():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT c.nom_client, c.prenom, COUNT(v.id_vente) AS nb_achats
            FROM ventes v
            JOIN clients c ON v.id_client = c.id_client
            GROUP BY c.id_client
            ORDER BY nb_achats DESC
            LIMIT 10
        """))
        return [dict(row._mapping) for row in result]
def get_clients_inscrits_apres(date: str):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM clients
            WHERE date_inscription > :date
        """), {"date": date})
        return [dict(row._mapping) for row in result]
def get_clients_par_genre():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT genre, COUNT(*) AS total 
            FROM clients 
            GROUP BY genre
        """))
        return [dict(row._mapping) for row in result]
def get_age_clients():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT nom_client, 
                   strftime('%Y', 'now') - strftime('%Y', date_naissance) AS age
            FROM clients
        """))
        return [dict(row._mapping) for row in result]
def get_clients_avec_achats_superieurs(montant):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT c.nom_client, SUM(v.montant_total) AS total
            FROM clients c
            JOIN ventes v ON c.id_client = v.id_client
            GROUP BY c.id_client
            HAVING total > :montant
        """), {"montant": montant})
        return [dict(row._mapping) for row in result]
def get_clients_ayant_recu_recompenses():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT nom_client, prenom, fidelite_recompenses
            FROM clients
            WHERE fidelite_recompenses > 0
        """))
        return [dict(row._mapping) for row in result]
def get_nombre_retours_par_client():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT c.nom_client, COUNT(r.id_retour) AS nombre_retours
            FROM clients c
            JOIN retours r ON c.id_client = r.id_client
            GROUP BY c.id_client
        """))
        return [dict(row._mapping) for row in result]
def get_produits_retournes_par_client():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT c.nom_client, p.nom_produit, r.date_retour
            FROM clients c
            JOIN retours r ON c.id_client = r.id_client
            JOIN produits p ON r.id_produit = p.id_produit
        """))
        return [dict(row._mapping) for row in result]
def get_ventes_par_ville():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT c.ville, COUNT(v.id_vente) AS total_ventes
            FROM clients c
            JOIN ventes v ON c.id_client = v.id_client
            GROUP BY c.ville
        """))
        return [dict(row._mapping) for row in result]

#Fonctions liées aux produits 
def get_top_10_produits_vendus():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT p.nom_produit, SUM(lv.quantite) AS total_vendus
            FROM lignes_ventes lv
            JOIN produits p ON lv.id_produit = p.id_produit
            GROUP BY p.nom_produit
            ORDER BY total_vendus DESC
            LIMIT 10
        """))
        return [dict(row._mapping) for row in result]   
def get_produits_plus_retournes():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT p.nom_produit, COUNT(*) AS nb_retours
            FROM retours r
            JOIN produits p ON r.id_produit = p.id_produit
            GROUP BY p.nom_produit
            ORDER BY nb_retours DESC
            LIMIT 5
        """))
        return [dict(row._mapping) for row in result]
def get_produits_rupture_stock():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT m.nom_magasin, p.nom_produit, s.quantite_stock
            FROM stocks s
            JOIN magasins m ON s.id_magasin = m.id_magasin
            JOIN produits p ON s.id_produit = p.id_produit
            WHERE s.quantite_stock = 0
        """))
        return [dict(row._mapping) for row in result]
def get_produits_sous_seuil_alerte():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT p.nom_produit, m.nom_magasin, s.quantite_stock, s.seuil_alerte
            FROM stocks s
            JOIN produits p ON s.id_produit = p.id_produit
            JOIN magasins m ON s.id_magasin = m.id_magasin
            WHERE s.quantite_stock < s.seuil_alerte
        """))
        return [dict(row._mapping) for row in result]
def get_produits_par_fournisseur():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT f.nom_fournisseur, COUNT(p.id_produit) AS nb_produits
            FROM fournisseurs f
            JOIN produits p ON f.id_fournisseur = p.id_fournisseur
            GROUP BY f.nom_fournisseur
        """))
        return [dict(row._mapping) for row in result]
def get_produits_plus_grand_montant_rembourse():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT p.nom_produit, SUM(r.montant_rembourse) AS total_rembourse
            FROM retours r
            JOIN produits p ON r.id_produit = p.id_produit
            GROUP BY p.id_produit
            ORDER BY total_rembourse DESC
            LIMIT 5
        """))
        return [dict(row._mapping) for row in result]
def get_produits_plus_stockes_par_magasin():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT m.nom_magasin, p.nom_produit, s.quantite_stock
            FROM stocks s
            JOIN produits p ON s.id_produit = p.id_produit
            JOIN magasins m ON s.id_magasin = m.id_magasin
            ORDER BY s.quantite_stock DESC
            LIMIT 10
        """))
        return [dict(row._mapping) for row in result]
def get_produits_jamais_vendus():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT p.nom_produit
            FROM produits p
            LEFT JOIN lignes_ventes lv ON p.id_produit = lv.id_produit
            WHERE lv.id_produit IS NULL
        """))
        return [dict(row._mapping) for row in result]
def get_top_3_categories_produits_vendus():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT p.categorie, SUM(lv.quantite) AS total_quantite
            FROM lignes_ventes lv
            JOIN produits p ON lv.id_produit = p.id_produit
            GROUP BY p.categorie
            ORDER BY total_quantite DESC
            LIMIT 3
        """))
        return [dict(row._mapping) for row in result]
def get_produits_ajoutes_apres(date_ajout):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT nom_produit, quantite 
            FROM produits 
            WHERE date_ajout > :date_ajout
        """), {"date_ajout": date_ajout})
        return [dict(row._mapping) for row in result]
def get_nombre_produits_par_categorie():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT categorie, COUNT(*) AS nb_produits 
            FROM produits 
            GROUP BY categorie
        """))
        return [dict(row._mapping) for row in result]
def get_produit_plus_cher():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM produits 
            ORDER BY prix_unitaire DESC 
            LIMIT 1
        """))
        return dict(result.fetchone()._mapping)
def get_produit_moins_cher():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM produits 
            ORDER BY prix_unitaire ASC 
            LIMIT 1
        """))
        return dict(result.fetchone()._mapping)
def get_produits_les_plus_vendus():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT p.nom_produit, SUM(lv.quantite) AS total_vendus
            FROM produits p
            JOIN lignes_ventes lv ON p.id_produit = lv.id_produit
            GROUP BY p.nom_produit
            ORDER BY total_vendus DESC
        """))
        return [dict(row._mapping) for row in result]

#Fonctions liées aux magasins / ventes
def get_chiffre_affaires_total():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT SUM(montant_total) AS chiffre_affaires_total FROM ventes
        """))
        row = result.fetchone()
        return [{"chiffre_affaires_total": row[0] if row and row[0] is not None else 0}]
def get_chiffre_affaires_par_mois():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DATE_FORMAT(date_vente, '%Y-%m') AS mois, SUM(montant_total) AS total
            FROM ventes
            GROUP BY mois
            ORDER BY mois
        """))
        return [dict(row._mapping) for row in result]  
def get_ventes_par_magasin():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT m.nom_magasin, SUM(v.montant_total) AS total_ventes
            FROM ventes v
            JOIN magasins m ON v.id_magasin = m.id_magasin
            GROUP BY m.nom_magasin
        """))
        return [dict(row._mapping) for row in result]  
def get_nb_ventes_par_canal():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT canal_vente, COUNT(*) AS nb_ventes
            FROM ventes
            GROUP BY canal_vente
        """))
        return [dict(row._mapping) for row in result]
def get_ventes_par_jour_semaine():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                DAYNAME(date_vente) AS jour_semaine, 
                SUM(montant_total) AS total_ventes
            FROM ventes
            GROUP BY jour_semaine
            ORDER BY FIELD(jour_semaine, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
        """))
        return [dict(row._mapping) for row in result]
def get_montant_moyen_vente_par_magasin():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT m.nom_magasin, AVG(v.montant_total) AS montant_moyen
            FROM ventes v
            JOIN magasins m ON v.id_magasin = m.id_magasin
            GROUP BY m.id_magasin, m.nom_magasin
        """))
        return [dict(row._mapping) for row in result]
def get_evolution_ventes_par_mois():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT YEAR(date_vente) AS annee, MONTH(date_vente) AS mois, COUNT(*) AS nb_ventes
            FROM ventes
            GROUP BY annee, mois
            ORDER BY annee, mois
        """))
        return [dict(row._mapping) for row in result]
def get_magasins_plus_faible_ca():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT m.nom_magasin, COALESCE(SUM(v.montant_total), 0) AS total_ventes
            FROM magasins m
            LEFT JOIN ventes v ON m.id_magasin = v.id_magasin
            GROUP BY m.id_magasin
            ORDER BY total_ventes ASC
            LIMIT 5
        """))
        return [dict(row._mapping) for row in result]

#Fonctions liées aux employés
def get_nombre_employes_par_magasin():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT m.nom_magasin, COUNT(e.id_employe) AS nombre_employes
            FROM employes e
            JOIN magasins m ON e.magasin_affecte = m.id_magasin
            GROUP BY m.nom_magasin
        """))
        return [dict(row._mapping) for row in result]
def get_employes_plus_ventes():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT e.nom_employe, COUNT(v.id_vente) AS nb_ventes
            FROM ventes v
            JOIN employes e ON v.id_employe = e.id_employe
            GROUP BY e.id_employe
            ORDER BY nb_ventes DESC
            LIMIT 10
        """))
        return [dict(row._mapping) for row in result]
def get_salaire_moyen_par_role():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT role, AVG(salaire) AS salaire_moyen
            FROM employes
            GROUP BY role
        """))
        return [dict(row._mapping) for row in result]
def get_employes_par_magasin(nom_magasin):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT nom_employe 
            FROM employes 
            WHERE magasin_affecte = :nom_magasin
        """), {"nom_magasin": nom_magasin})
        return [dict(row._mapping) for row in result]
def get_employes_par_role(role):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT nom_employe 
            FROM employes 
            WHERE role = :role
        """), {"role": role})
        return [dict(row._mapping) for row in result]
def get_ventes_par_employe():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT e.nom_employe, COUNT(v.id_vente) AS nombre_ventes
            FROM employes e
            JOIN ventes v ON e.id_employe = v.id_employe
            GROUP BY e.nom_employe
        """))
        return [dict(row._mapping) for row in result]
def get_chiffre_affaire_par_employe():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT e.nom_employe, SUM(v.montant_total) AS chiffre_affaires
            FROM employes e
            JOIN ventes v ON e.id_employe = v.id_employe
            GROUP BY e.nom_employe
        """))
        return [dict(row._mapping) for row in result]
def get_employes_ventes_apres(date_vente):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT e.nom_employe
            FROM employes e
            JOIN ventes v ON e.id_employe = v.id_employe
            WHERE v.date_vente > :date_vente
        """), {"date_vente": date_vente})
        return [dict(row._mapping) for row in result]

# Fonctions liées aux fournisseurs
def get_fournisseur_plus_stock():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT f.nom_fournisseur, SUM(s.quantite_stock) AS total_stock
            FROM fournisseurs f
            JOIN produits p ON f.id_fournisseur = p.id_fournisseur
            JOIN stocks s ON p.id_produit = s.id_produit
            GROUP BY f.nom_fournisseur
            ORDER BY total_stock DESC
        """))
        return [dict(row._mapping) for row in result]

#Fonctions liées aux paiements
def get_repartition_par_paiement():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT methode_paiement, COUNT(*) AS nb_ventes
            FROM ventes
            GROUP BY methode_paiement
        """))
        return [dict(row._mapping) for row in result]
def get_all_methodes_paiement():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT methode_paiement FROM ventes
        """))
        return [dict(row._mapping) for row in result]
def count_ventes_par_methode():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT methode_paiement, COUNT(*) AS nombre_ventes
            FROM ventes
            GROUP BY methode_paiement
        """))
        return [dict(row._mapping) for row in result]
def sum_ventes_par_methode():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT methode_paiement, SUM(montant_total) AS total_paiements
            FROM ventes
            GROUP BY methode_paiement
        """))
        return [dict(row._mapping) for row in result]
def paiements_par_jour():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DATE(date_vente) AS jour, methode_paiement, SUM(montant_total) AS total
            FROM ventes
            GROUP BY DATE(date_vente), methode_paiement
            ORDER BY jour
        """))
        return [dict(row._mapping) for row in result]
def paiements_par_mois():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT YEAR(date_vente) AS annee, MONTH(date_vente) AS mois, methode_paiement, SUM(montant_total) AS total
            FROM ventes
            GROUP BY annee, mois, methode_paiement
            ORDER BY annee, mois
        """))
        return [dict(row._mapping) for row in result]
def get_ventes_par_methode(methode):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM ventes
            WHERE methode_paiement = :methode
        """), {"methode": methode})
        return [dict(row._mapping) for row in result]
def get_ventes_superieures_a(montant):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM ventes
            WHERE montant_total > :montant
        """), {"montant": montant})
        return [dict(row._mapping) for row in result]

##Fonctions liées aux  retours
def get_pourcentage_retours():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM retours) * 100.0 / NULLIF((SELECT COUNT(*) FROM lignes_ventes), 0) AS pourcentage_retours
        """))
        row = result.fetchone()
        return {"pourcentage_retours": float(row[0]) if row and row[0] is not None else 0.0}
def get_retours_par_statut():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT statut_retour, COUNT(*) AS nombre_retours
            FROM retours
            GROUP BY statut_retour
        """))
        return [dict(row._mapping) for row in result]
def get_raisons_retour_frequentes():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT raison_retour, COUNT(*) AS nb_retours
            FROM retours
            GROUP BY raison_retour
            ORDER BY nb_retours DESC
            LIMIT 5
        """))
        return [dict(row._mapping) for row in result]
def get_nombre_retours_par_produit():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT p.nom_produit, COUNT(*) AS nombre_retours
            FROM retours r
            JOIN produits p ON r.id_produit = p.id_produit
            GROUP BY p.nom_produit
        """))
        return [dict(row._mapping) for row in result]
def get_retours_par_statut(statut: str):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM retours
            WHERE statut_retour = :statut
        """), {"statut": statut})
        return [dict(row._mapping) for row in result]

intent_function_map = {
  #Fonctions liées aux clients
"get_clients_par_annee": get_clients_par_annee,
"get_nouveaux_clients_par_mois": get_nouveaux_clients_par_mois,
"get_clients_plus_fidelite": get_clients_plus_fidelite,
"get_clients_plus_achats": get_clients_plus_achats,
"get_clients_ayant_recu_recompenses": get_clients_ayant_recu_recompenses,
"get_nombre_retours_par_client": get_nombre_retours_par_client,
"get_produits_retournes_par_client":get_produits_retournes_par_client,
"get_clients_inscrits_apres": get_clients_inscrits_apres,
"get_clients_par_genre": get_clients_par_genre,
"get_age_clients": get_age_clients,
"get_ventes_par_ville":  get_ventes_par_ville,
"get_clients_achats_superieurs": get_clients_avec_achats_superieurs,



#Fonctions liées aux produits 
"get_top_10_produits_vendus": get_top_10_produits_vendus,
"get_produits_plus_retournes": get_produits_plus_retournes,
"get_produits_rupture_stock": get_produits_rupture_stock,
"get_produits_sous_seuil_alerte": get_produits_sous_seuil_alerte,
"get_produits_par_fournisseur": get_produits_par_fournisseur,
"get_produits_plus_grand_montant_rembourse": get_produits_plus_grand_montant_rembourse,
"get_produits_plus_stockes_par_magasin": get_produits_plus_stockes_par_magasin,
"get_produits_jamais_vendus": get_produits_jamais_vendus,
"get_top_3_categories_produits_vendus": get_top_3_categories_produits_vendus,
"get_produits_apres_date": get_produits_ajoutes_apres,
"get_produits_par_categorie": get_nombre_produits_par_categorie,
"get_produit_plus_cher": get_produit_plus_cher,
"get_produit_moins_cher": get_produit_moins_cher,
"get_produits_les_plus_vendus": get_produits_les_plus_vendus,


#Fonctions liées aux magasins / ventes 
"get_chiffre_affaires_total": get_chiffre_affaires_total,
"get_chiffre_affaires_par_mois": get_chiffre_affaires_par_mois,
"get_ventes_par_magasin": get_ventes_par_magasin,
"get_montant_moyen_vente_par_magasin": get_montant_moyen_vente_par_magasin,
"get_magasins_plus_faible_ca": get_magasins_plus_faible_ca,
"get_nb_ventes_par_canal": get_nb_ventes_par_canal,
"get_ventes_par_jour_semaine": get_ventes_par_jour_semaine,
"get_evolution_ventes_par_mois": get_evolution_ventes_par_mois,


#Fonctions liées aux employés
"get_employes_plus_ventes": get_employes_plus_ventes,
"get_salaire_moyen_par_role": get_salaire_moyen_par_role,
"get_employes_par_magasin": get_employes_par_magasin,
"get_employes_par_role": get_employes_par_role,
"get_nombre_employes_par_magasin": get_nombre_employes_par_magasin,
"get_ventes_par_employe": get_ventes_par_employe,
"get_chiffre_affaire_par_employe": get_chiffre_affaire_par_employe,
"get_employes_ventes_apres": get_employes_ventes_apres,


# Fonctions liées aux fournisseurs
"get_fournisseur_plus_stock": get_fournisseur_plus_stock,

#Fonctions liées aux paiements
"get_repartition_par_paiement": get_repartition_par_paiement,
"get_all_methodes_paiement": get_all_methodes_paiement,
"count_ventes_par_methode": count_ventes_par_methode,
"sum_ventes_par_methode": sum_ventes_par_methode,
"paiements_par_jour": paiements_par_jour,
"paiements_par_mois":paiements_par_mois,
"get_ventes_par_methode": get_ventes_par_methode,
"get_ventes_superieures_a": get_ventes_superieures_a,

##Fonctions liées aux  retours
"get_pourcentage_retours": get_pourcentage_retours,
"get_retours_par_statut": get_retours_par_statut,
"get_raisons_retour_frequentes": get_raisons_retour_frequentes,
"get_nombre_retours_par_produit":get_nombre_retours_par_produit,
"get_retours_par_statut": get_retours_par_statut,



}
