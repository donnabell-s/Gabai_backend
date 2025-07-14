import os
import joblib
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from firebase_admin import firestore

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'assessment', 'models')

model_inattentive = joblib.load(os.path.join(MODEL_DIR, 'rf_model_Inattentive_Result.pkl'))
model_hyperactive = joblib.load(os.path.join(MODEL_DIR, 'rf_model_Hyperactive_Impulsive_Result.pkl'))
model_oppositional = joblib.load(os.path.join(MODEL_DIR, 'rf_model_Oppositional_Defiant_Result.pkl'))

FEATURE_COLUMNS = [
    'Age', 'Gender', 'Family Structure', 'Screen Access', 
    'Access Level', 'Frequency Level', 'Content Level', 'Interactivity Level'
]

@csrf_exempt
def predict_targets(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')

            if not user_id:
                return JsonResponse({'error': 'Missing user_id'}, status=400)

            db = firestore.client()
            doc_ref = db.collection("children").document(user_id)
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
                profile['interactivity_level'],
            ]

            X_input = pd.DataFrame([features], columns=FEATURE_COLUMNS)

            pred_inattentive = model_inattentive.predict(X_input)[0]
            pred_hyperactive = model_hyperactive.predict(X_input)[0]
            pred_oppositional = model_oppositional.predict(X_input)[0]

            doc_ref.update({
                'inattentive_result': int(pred_inattentive),
                'hyperactive_result': int(pred_hyperactive),
                'oppositional_result': int(pred_oppositional),
            })

            return JsonResponse({
                'user_id': user_id,
                'profile_name': profile.get('name'),
                'predictions': {
                    'Inattentive Result': int(pred_inattentive),
                    'Hyperactive/Impulsive Result': int(pred_hyperactive),
                    'Oppositional/Defiant Result': int(pred_oppositional),
                }
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'message': 'Only POST method is allowed.'}, status=405)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')

            if not user_id:
                return JsonResponse({'error': 'Missing user_id'}, status=400)

            db = firestore.client()
            doc_ref = db.collection("children").document(user_id)
            doc = doc_ref.get()

            if not doc.exists:
                return JsonResponse({'error': f'User ID {user_id} not found.'}, status=404)

            profile = doc.to_dict()

            # Extract and map features
            features = [
                profile['age'],
                profile['gender'],
                1,  # Default Family Structure, adjust if available
                profile['screen_access'],
                profile['access_level'],
                profile['frequency_level'],
                profile['content_level'],
                profile['interactivity_level'],
            ]

            X_input = pd.DataFrame([features], columns=FEATURE_COLUMNS)

            pred_inattentive = model_inattentive.predict(X_input)[0]
            pred_hyperactive = model_hyperactive.predict(X_input)[0]
            pred_oppositional = model_oppositional.predict(X_input)[0]

            # Optional: save results back to Firebase
            doc_ref.update({
                'inattentive_result': int(pred_inattentive),
                'hyperactive_result': int(pred_hyperactive),
                'oppositional_result': int(pred_oppositional),
            })

            return JsonResponse({
                'user_id': user_id,
                'predictions': {
                    'Inattentive Result': int(pred_inattentive),
                    'Hyperactive/Impulsive Result': int(pred_hyperactive),
                    'Oppositional/Defiant Result': int(pred_oppositional),
                }
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'message': 'Only POST method is allowed.'}, status=405)