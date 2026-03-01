from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .utils import predict_disease_from_symptoms
from .models import DiseasePrediction
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from .utils import SYMPTOM_COLUMNS

@csrf_exempt
def predict_disease(request):
    if request.method == "POST":
        data = json.loads(request.body)
        symptoms = data.get("symptoms", [])

        result = predict_disease_from_symptoms(symptoms)

        if not result:
            return JsonResponse({"error": "No valid symptoms"}, status=400)

        # ✅ SAVE TO DATABASE
        DiseasePrediction.objects.create(
            user=request.user if request.user.is_authenticated else None,
            symptoms=", ".join(symptoms),
            predicted_disease=result["disease"],
            severity=result["severity"]
        )

        return JsonResponse(result)


@login_required
def prediction_history(request):

    predictions = DiseasePrediction.objects.filter(
        user=request.user
    ).order_by("-created_at")

    data = [
        {
            "symptoms": p.symptoms,
            "disease": p.predicted_disease,
            "severity": p.severity,
            "date": p.created_at.strftime("%d %b %Y %H:%M")
        }
        for p in predictions
    ]

    return JsonResponse(data, safe=False)

def get_symptoms(request):

    symptoms = [
        s.replace("symptom_", "").replace("_", " ").title()
        for s in SYMPTOM_COLUMNS
    ]

    return JsonResponse(symptoms, safe=False)