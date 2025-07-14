import os
import django
import firebase_admin
from firebase_admin import credentials, firestore

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TechXplore.settings")
django.setup()

if not firebase_admin._apps:
    cred = credentials.Certificate("credentials/firebase-key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


children_ref = db.collection("children")
existing_docs = children_ref.stream()

print("Deleting existing child profiles...")
for doc in existing_docs:
    doc.reference.delete()
    print(f"Deleted: {doc.id}")

child_profiles = {
    "1": {
        "name": "Jamie",
        "age": 9,
        "gender": 1,  # female
        "family_structure": 0, 
        "screen_access": 1,    
        "access_level": 1,
        "frequency_level": 1,
        "content_level": 1,
        "interactivity_level": 1,
        "inattentive_result": 0,
        "hyperactive_result": 1,
        "oppositional_result": 0
    },
    "2": {
        "name": "Mika",
        "age": 10,
        "gender": 0,  # male
        "family_structure": 2,  
        "screen_access": 1,   
        "access_level": 0,
        "frequency_level": 0,
        "content_level": 0,
        "interactivity_level": 0,
        "inattentive_result": 2,
        "hyperactive_result": 2,
        "oppositional_result": 1
    }
}


print("\nInitializing new child profiles...")
for user_id, profile in child_profiles.items():
    doc_ref = db.collection("children").document(user_id)
    doc_ref.set(profile)
    print(f"Initialized child profile for user_id={user_id}")
