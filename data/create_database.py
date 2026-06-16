import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_PATH


def create_database():
    """Crée la base de données SQLite avec des données fictives."""

    print(f"Création de la base de données : {DB_PATH}")

    # Crée le dossier data si nécessaire
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ─── Table : employes ─────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT NOT NULL,
            prenom      TEXT NOT NULL,
            departement TEXT NOT NULL,
            poste       TEXT NOT NULL,
            salaire     REAL NOT NULL,
            date_embauche TEXT NOT NULL,
            email       TEXT NOT NULL
        )
    """)

    employes = [
        ("Bakkari",   "Abdelkhalek", "Direction",    "CEO",                    15000, "2020-01-15", "a.bakkari@smartovate.com"),
        ("Martin",    "Sophie",      "RH",           "DRH",                    9000,  "2020-03-01", "s.martin@smartovate.com"),
        ("Dubois",    "Pierre",      "Tech",         "Lead Developer",          8500,  "2021-06-15", "p.dubois@smartovate.com"),
        ("Leroy",     "Marie",       "Tech",         "Data Scientist",          7500,  "2021-09-01", "m.leroy@smartovate.com"),
        ("Bernard",   "Thomas",      "Commercial",   "Directeur Commercial",    8000,  "2020-07-01", "t.bernard@smartovate.com"),
        ("Petit",     "Julie",       "Commercial",   "Account Manager",         5500,  "2022-01-10", "j.petit@smartovate.com"),
        ("Moreau",    "Lucas",       "Tech",         "DevOps Engineer",         7000,  "2022-03-15", "l.moreau@smartovate.com"),
        ("Simon",     "Emma",        "Marketing",    "Marketing Manager",       6500,  "2021-11-01", "e.simon@smartovate.com"),
        ("Laurent",   "Nicolas",     "Tech",         "Backend Developer",       6800,  "2022-05-01", "n.laurent@smartovate.com"),
        ("Michel",    "Camille",     "RH",           "HR Manager",              5800,  "2023-01-15", "c.michel@smartovate.com"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO employes
        (nom, prenom, departement, poste, salaire, date_embauche, email)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, employes)

    # ─── Table : projets ──────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT NOT NULL,
            client      TEXT NOT NULL,
            statut      TEXT NOT NULL,
            budget      REAL NOT NULL,
            date_debut  TEXT NOT NULL,
            date_fin    TEXT,
            responsable TEXT NOT NULL
        )
    """)

    projets = [
        ("Agent IA Bedrock",     "SMARTOVATE",   "En cours",  50000,  "2026-06-01", None,         "Dubois Pierre"),
        ("Refonte Site Web",     "Client A",     "Terminé",   15000,  "2025-09-01", "2025-12-31", "Simon Emma"),
        ("Plateforme E-commerce","Client B",     "En cours",  80000,  "2026-01-15", None,         "Laurent Nicolas"),
        ("App Mobile RH",        "Client C",     "En attente",35000,  "2026-07-01", None,         "Moreau Lucas"),
        ("Data Pipeline",        "Client D",     "Terminé",   25000,  "2025-06-01", "2025-11-30", "Leroy Marie"),
        ("CRM Personnalisé",     "Client E",     "En cours",  45000,  "2026-03-01", None,         "Petit Julie"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO projets
        (nom, client, statut, budget, date_debut, date_fin, responsable)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, projets)

    # ─── Table : ventes ───────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            produit     TEXT NOT NULL,
            client      TEXT NOT NULL,
            montant     REAL NOT NULL,
            date_vente  TEXT NOT NULL,
            vendeur     TEXT NOT NULL,
            statut      TEXT NOT NULL
        )
    """)

    ventes = [
        ("Licence IA Pro",      "Client A", 12000, "2026-01-10", "Bernard Thomas", "Payé"),
        ("Consulting IA",       "Client B", 8500,  "2026-01-25", "Petit Julie",    "Payé"),
        ("Formation LangChain", "Client C", 3500,  "2026-02-05", "Bernard Thomas", "Payé"),
        ("Licence IA Pro",      "Client D", 12000, "2026-02-20", "Petit Julie",    "En attente"),
        ("Consulting IA",       "Client E", 9500,  "2026-03-10", "Bernard Thomas", "Payé"),
        ("Développement API",   "Client F", 25000, "2026-03-25", "Petit Julie",    "En cours"),
        ("Licence IA Pro",      "Client G", 12000, "2026-04-15", "Bernard Thomas", "Payé"),
        ("Formation AWS",       "Client H", 4500,  "2026-04-28", "Petit Julie",    "Payé"),
        ("Consulting IA",       "Client I", 7500,  "2026-05-10", "Bernard Thomas", "En attente"),
        ("Développement Agent", "Client J", 35000, "2026-05-20", "Petit Julie",    "En cours"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO ventes
        (produit, client, montant, date_vente, vendeur, statut)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ventes)

    conn.commit()
    conn.close()

    print("Base de données créée avec succès ✅")
    print("  Tables créées : employes, projets, ventes")
    print(f"  Fichier : {DB_PATH}")


if __name__ == "__main__":
    create_database()