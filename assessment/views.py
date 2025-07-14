import os
import joblib
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

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
            features = data.get('features')  
            
            if not features or len(features) != len(FEATURE_COLUMNS):
                return JsonResponse({'error': 'Invalid input. Provide all required features.'}, status=400)
            
            X_input = pd.DataFrame([features], columns=FEATURE_COLUMNS)
            
            pred_inattentive = model_inattentive.predict(X_input)[0]
            pred_hyperactive = model_hyperactive.predict(X_input)[0]
            pred_oppositional = model_oppositional.predict(X_input)[0]

            return JsonResponse({
                'Inattentive Result': int(pred_inattentive),
                'Hyperactive/Impulsive Result': int(pred_hyperactive),
                'Oppositional/Defiant Result': int(pred_oppositional),
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'message': 'Only POST method is allowed.'}, status=405)
