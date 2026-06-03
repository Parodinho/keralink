#!/usr/bin/env python
"""
Script de correction des guest_id dupliqués.
Placez ce fichier dans C:\Environnement DJANGO\keralink_project\
(même dossier que manage.py) puis exécutez :
    python fix_db.py
"""
import os
import sys
import uuid
import sqlite3

# ✅ Chemin vers votre base de données
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'db.sqlite3')

if not os.path.exists(DB_PATH):
    print(f"❌ Base de données introuvable : {DB_PATH}")
    sys.exit(1)

conn   = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Lire tous les profils
cursor.execute("SELECT id, nom_complet, guest_id FROM voyageurs_profil ORDER BY id")
profils = cursor.fetchall()

print(f"=== {len(profils)} profil(s) trouvé(s) ===\n")

seen = set()
corriges = 0

for profil_id, nom, guest_id in profils:
    besoin_correction = (
        not guest_id              # NULL
        or guest_id.strip() == '' # chaîne vide
        or guest_id in seen       # doublon
    )
    if besoin_correction:
        nouveau = str(uuid.uuid4())
        cursor.execute(
            "UPDATE voyageurs_profil SET guest_id = ? WHERE id = ?",
            (nouveau, profil_id)
        )
        print(f"  ✅ Profil {profil_id} ({nom})")
        print(f"     Ancien : {repr(guest_id)}")
        print(f"     Nouveau: {nouveau}\n")
        seen.add(nouveau)
        corriges += 1
    else:
        print(f"  ✓  Profil {profil_id} ({nom}) — guest_id OK")
        seen.add(guest_id)

conn.commit()
conn.close()

print(f"\n=== ✅ {corriges} correction(s) effectuée(s) ===")
print("\nMaintenant exécutez dans le terminal :")
print("  python manage.py migrate")