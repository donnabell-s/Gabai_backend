import os
import django
import firebase_admin
from firebase_admin import credentials, firestore
import json
import csv
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TechXplore.settings")
django.setup()

if not firebase_admin._apps:
    cred = credentials.Certificate("credentials/firebase-key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

nudges_ref = db.collection("nudges").stream()
nudges_raw = [doc.to_dict() for doc in nudges_ref]

nudges = []
for item in nudges_raw:
    flat = {
        "text": item.get("text", "")
    }
    profile = item.get("target_profile", {})
    for key, value in profile.items():
        flat[key] = value
    nudges.append(flat)

with open("nudges.json", "w", encoding="utf-8") as f_json:
    json.dump(nudges, f_json, ensure_ascii=False, indent=2)
print("Exported to nudges.json")

csv_fields = sorted(nudges[0].keys()) if nudges else []

with open("nudges.csv", "w", newline="", encoding="utf-8") as f_csv:
    writer = csv.DictWriter(f_csv, fieldnames=csv_fields)
    writer.writeheader()
    for nudge in nudges:
        writer.writerow(nudge)
print("Exported to nudges.csv")

df = pd.DataFrame(nudges)
df.to_excel("nudges.xlsx", index=False)
print("Exported to nudges.xlsx")
