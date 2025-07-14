import os
import json
import re
import django
import requests
import firebase_admin
from firebase_admin import credentials, firestore

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TechXplore.settings")
django.setup()

from django.conf import settings

# Initialize Firebase if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("credentials/firebase-key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

print("Deleting previous nudges from Firestore...")
nudges_ref = db.collection("nudges").stream()
for doc in nudges_ref:
    doc.reference.delete()
    print(f"Deleted: {doc.id}")

headers = {
    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}

payload_template = {
    "model": "deepseek-chat",
    "temperature": 0.7,
    "messages": []
}

# ✅ Modified prompt with new tag rules and added 'family_structure'
llm_prompt = """
You are generating short, offline, proactive nudges for children aged 6 to 15. Each nudge should support cognitive or emotional development and match a specific behavioral profile.

Each nudge must:
- Be age-appropriate (for ages 6–15)
- Be actionable (drawing, stretching, reflecting, moving, etc.)
- Help with self-regulation, focus, or emotion
- Include a `target_profile` describing the type of child this nudge is designed for

Return 20 nudges in this exact JSON structure:

[
  {
    "text": "example...",
    "target_profile": {
      "age": 9,
      "gender": 1,
      "family_structure": 0,
      "screen_access": 1,
      "access_level": 1,
      "frequency_level": 1,
      "content_level": 1,
      "interactivity_level": 1,
      "inattentive_result": 0,
      "hyperactive_result": 2,
      "oppositional_result": 0
    }
  }
]

Tag rules for `target_profile`:
- gender: 0 = male, 1 = female
- family_structure:
  - 0 = nuclear
  - 1 = single-parent
  - 2 = extended or other
- screen_access:
  - 0 = no access
  - 1 = limited access
  - 2 = unrestricted access
- access_level: 1 = high, 0 = low
- frequency_level: 1 = high, 0 = low
- content_level: 1 = low content quality, 0 = high
- interactivity_level: 1 = low interactivity, 0 = high
- inattentive_result, hyperactive_result, oppositional_result:
  - 0 = symptoms not clinically significant
  - 1 = mild symptoms
  - 2 = severe symptoms

Only return the raw JSON inside a markdown code block like: ```json ... ```
"""

all_nudges = []

for batch_num in range(5):
    print(f"\nGenerating batch {batch_num + 1} of 5...")

    payload = payload_template.copy()
    payload["messages"] = [{"role": "user", "content": llm_prompt}]

    try:
        response = requests.post(settings.DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        match = re.search(r"```json\s*(\[.*?\])\s*```", content, re.DOTALL)
        if not match:
            print("Could not extract JSON. Raw content:\n", content)
            continue

        nudges_batch = json.loads(match.group(1))
        print(f"Received {len(nudges_batch)} nudges.")
        all_nudges.extend(nudges_batch)

    except Exception as e:
        print(f"Error in batch {batch_num + 1}: {e}")
        continue

print(f"\nSaving {len(all_nudges)} nudges to Firestore...")
for nudge in all_nudges:
    db.collection("nudges").add(nudge)
    print(f"Saved: {nudge['text']}")
