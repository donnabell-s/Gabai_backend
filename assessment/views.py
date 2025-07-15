

import os
import json
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import joblib
from firebase_admin import firestore

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'assessment', 'models')
NUDGES_FILE = os.path.join(BASE_DIR, 'nudges.json')  # make sure this is the correct path

# Load models
model_inattentive = joblib.load(os.path.join(MODEL_DIR, 'rf_model_Inattentive_Result.pkl'))
model_hyperactive = joblib.load(os.path.join(MODEL_DIR, 'rf_model_Hyperactive_Impulsive_Result.pkl'))
model_oppositional = joblib.load(os.path.join(MODEL_DIR, 'rf_model_Oppositional_Defiant_Result.pkl'))

FEATURE_COLUMNS = [
    'Age', 'Gender', 'Family Structure', 'Screen Access',
    'Access Level', 'Frequency Level', 'Content Level', 'Interactivity Level'
]

def get_matching_nudges(profile):
    try:
        with open(NUDGES_FILE, 'r') as file:
            all_nudges = json.load(file)

        weights = {
            'age': 1.0,
            'gender': 1.0,
            'family_structure': 1.0,
            'screen_access': 1.0,
            'access_level': 1.0,
            'frequency_level': 1.0,
            'content_level': 1.0,
            'interactivity_level': 1.0,
            'inattentive_result': 1.0,
            'hyperactive_result': 1.0,
            'oppositional_result': 1.0,
        }

        max_score = sum(weights.values())
        top_nudges = []

        for nudge in all_nudges:
            score = 0

            # Age difference logic
            if 'age' in nudge and 'age' in profile:
                age_diff = abs(nudge['age'] - profile['age'])
                if age_diff == 0:
                    score += weights['age']
                elif age_diff <= 2:
                    score += weights['age'] * (1 - age_diff / 4)

            for field in ['gender', 'family_structure', 'screen_access', 'access_level',
                          'frequency_level', 'content_level', 'interactivity_level']:
                if nudge.get(field) == profile.get(field):
                    score += weights[field]

            # Similarity for results (scaled difference)
            for symptom in ['inattentive_result', 'hyperactive_result', 'oppositional_result']:
                n_val = nudge.get(symptom)
                p_val = profile.get(symptom)
                if n_val is not None and p_val is not None:
                    score += weights[symptom] * (1 - abs(n_val - p_val) / 3)

            match_rate = round(score / max_score, 2)

            top_nudges.append({
                'text': nudge['text'],
                'match': match_rate
            })

        top_nudges.sort(key=lambda x: x['match'], reverse=True)
        return top_nudges[:10]

    except Exception as e:
        print(f"❌ Error in get_matching_nudges: {e}")
        return []
    


# ✅ Main View
@csrf_exempt
def predict_targets(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Only POST method is allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')

        if not user_id:
            return JsonResponse({'error': 'Missing user_id'}, status=400)

        db = firestore.client()
        doc_ref = db.collection("children").document(str(user_id))
        doc = doc_ref.get()

        if not doc.exists:
            return JsonResponse({'error': f'User ID {user_id} not found.'}, status=404)

        profile = doc.to_dict()
        required_keys = [
            'age', 'gender', 'family_structure', 'screen_access',
            'access_level', 'frequency_level', 'content_level', 'interactivity_level'
        ]
        for key in required_keys:
            if key not in profile:
                return JsonResponse({'error': f'Missing field in profile: {key}'}, status=400)

        features = [
            profile['age'],
            profile['gender'],
            profile['family_structure'],
            profile['screen_access'],
            profile['access_level'],
            profile['frequency_level'],
            profile['content_level'],
            profile['interactivity_level']
        ]
        X_input = pd.DataFrame([features], columns=FEATURE_COLUMNS)

        # Predict
        pred_inattentive = int(model_inattentive.predict(X_input)[0])
        pred_hyperactive = int(model_hyperactive.predict(X_input)[0])
        pred_oppositional = int(model_oppositional.predict(X_input)[0])

        # Update Firestore
        doc_ref.update({
            'inattentive_result': pred_inattentive,
            'hyperactive_result': pred_hyperactive,
            'oppositional_result': pred_oppositional
        })

        updated = doc_ref.get().to_dict()

        # Ordered output
        ordered_profile = {
            "name": updated.get("name"),
            "age": updated.get("age"),
            "gender": updated.get("gender"),
            "family_structure": updated.get("family_structure"),
            "screen_access": updated.get("screen_access"),
            "access_level": updated.get("access_level"),
            "frequency_level": updated.get("frequency_level"),
            "content_level": updated.get("content_level"),
            "interactivity_level": updated.get("interactivity_level"),
            "inattentive_result": updated.get("inattentive_result"),
            "hyperactive_result": updated.get("hyperactive_result"),
            "oppositional_result": updated.get("oppositional_result")
        }

        # Match nudges
        nudges = get_matching_nudges(ordered_profile)

        return JsonResponse({
            "user_id": user_id,
            "profile": ordered_profile,
            "nudges": nudges
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
