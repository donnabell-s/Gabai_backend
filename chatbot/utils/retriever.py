from chatbot.utils.firebase_config import db
from chatbot.utils.knowledge_base import knowledge_map

def get_child_profile(user_id):
    try:
        doc_ref = db.collection("children").document(str(user_id))
        doc = doc_ref.get()

        if not doc.exists:
            raise ValueError(f"No child profile found for user_id: {user_id}")

        return doc.to_dict()

    except Exception as e:
        print("Firebase error:", e)
        raise


def get_knowledge_chunks(query):
    query = query.lower()
    chunks = []

    for keyword, tips in knowledge_map.items():
        if keyword in query:
            chunks.extend(tips)

    return "\n".join(chunks)