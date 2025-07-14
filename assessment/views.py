import os
import json
import joblib
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from firebase_admin import firestore

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'assessment', 'models')

# Load models once
model_inattentive = joblib.load(os.path.join(MODEL_DIR, 'rf_model_Inattentive_Result.pkl'))
model_hyperactive = joblib.load(os.path.join(MODEL_DIR, 'rf_model_Hyperactive_Impulsive_Result.pkl'))
model_oppositional = joblib.load(os.path.join(MODEL_DIR, 'rf_model_Oppositional_Defiant_Result.pkl'))

FEATURE_COLUMNS = [
    'Age', 'Gender', 'Family Structure', 'Screen Access',
    'Access Level', 'Frequency Level', 'Content Level', 'Interactivity Level'
]

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

        # Prepare input for prediction
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

        # Predict behavioral scores
        pred_inattentive = int(model_inattentive.predict(X_input)[0])
        pred_hyperactive = int(model_hyperactive.predict(X_input)[0])
        pred_oppositional = int(model_oppositional.predict(X_input)[0])

        # Update Firestore with predictions
        doc_ref.update({
            'inattentive_result': pred_inattentive,
            'hyperactive_result': pred_hyperactive,
            'oppositional_result': pred_oppositional
        })

        # Reload updated profile
        updated = doc_ref.get().to_dict()

        # Return ordered profile
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
            "oppositional_result": updated.get("oppositional_result"),
        }

        return JsonResponse({
            "user_id": user_id,
            "profile": ordered_profile
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
