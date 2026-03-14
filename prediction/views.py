import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import DiseasePrediction
from .symptom_extractor import extract_symptoms
from .utils import SYMPTOM_COLUMNS, SYMPTOM_NAMES, predict_disease_from_symptoms
from .vision import analyze_uploaded_image, validate_uploaded_image

MEDICAL_DISCLAIMER = "This result is only a prediction and not a confirmed medical diagnosis."


def _should_recommend_doctor(result):
    severity = str(result.get("severity", "")).strip().lower()
    advice = str(result.get("advice", "")).strip().lower()

    warning_terms = [
        "doctor",
        "medical attention",
        "urgent",
        "immediate",
        "hospital",
        "consult",
    ]

    return severity in {"high", "severe"} or any(term in advice for term in warning_terms)


def _translate_to_english(message):
    if not message:
        return message

    try:
        from googletrans import Translator

        translator = Translator()
        translated = translator.translate(message, dest="en")
        return translated.text or message
    except Exception:
        return message


def _save_prediction(request, symptoms, result, uploaded_image=None, image_analysis=None):
    DiseasePrediction.objects.create(
        user=request.user if request.user.is_authenticated else None,
        symptoms=", ".join(symptoms),
        predicted_disease=result["disease"],
        severity=result["severity"],
        uploaded_image=uploaded_image,
        image_analysis=image_analysis,
    )


def _normalize_extra_symptoms(raw_symptoms):
    if not isinstance(raw_symptoms, list):
        return []

    valid_symptoms = {name.lower(): name for name in SYMPTOM_NAMES}
    normalized = []

    for symptom in raw_symptoms:
        key = str(symptom).strip().lower()
        if not key:
            continue

        mapped = valid_symptoms.get(key)
        if mapped:
            normalized.append(mapped)

    return normalized


@csrf_exempt
def predict_disease(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    symptoms = data.get("symptoms", [])
    if not isinstance(symptoms, list):
        return JsonResponse({"error": "Symptoms must be a list"}, status=400)

    symptoms = [str(symptom).strip() for symptom in symptoms if str(symptom).strip()]
    if not symptoms:
        return JsonResponse({"error": "No valid symptoms"}, status=400)

    result = predict_disease_from_symptoms(symptoms)
    if not result:
        return JsonResponse({"error": "No valid symptoms"}, status=400)

    result["recommend_doctor_consultation"] = _should_recommend_doctor(result)
    _save_prediction(request, symptoms, result)
    return JsonResponse(result)


@csrf_exempt
def chat_predict(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST request required"}, status=405)

    if request.content_type and request.content_type.startswith("multipart/form-data"):
        data = request.POST
    else:
        try:
            data = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    message = str(data.get("message", "")).strip()
    uploaded_image = request.FILES.get("image")
    image_analysis = None
    image_symptoms = []

    if uploaded_image:
        validation_error = validate_uploaded_image(uploaded_image)
        if validation_error:
            return JsonResponse({"success": False, "error": validation_error}, status=400)

        image_analysis = analyze_uploaded_image(uploaded_image)
        image_symptoms = _normalize_extra_symptoms(image_analysis.get("symptoms", []))

    if not message and not image_symptoms:
        return JsonResponse({"success": False, "message": "Message or image hints are required"}, status=400)

    translated = _translate_to_english(message) if message else ""
    symptoms = extract_symptoms(translated, SYMPTOM_NAMES) if translated else []
    symptoms.extend(image_symptoms)
    symptoms = list(dict.fromkeys(symptoms))

    if not symptoms:
        return JsonResponse(
            {
                "success": False,
                "error": "No symptoms detected from the description.",
                "disclaimer": MEDICAL_DISCLAIMER,
            },
            status=400,
        )

    prediction = predict_disease_from_symptoms(symptoms)
    if not prediction:
        return JsonResponse(
            {
                "success": False,
                "error": "Prediction failed.",
                "disclaimer": MEDICAL_DISCLAIMER,
            },
            status=400,
        )

    _save_prediction(
        request,
        symptoms,
        prediction,
        uploaded_image=uploaded_image,
        image_analysis=image_analysis,
    )

    return JsonResponse(
        {
            "success": True,
            "translated_text": translated,
            "detected_symptoms": symptoms,
            "matched_symptoms": symptoms,
            "image_symptoms": image_symptoms,
            "image_analysis": image_analysis,
            "disease": prediction["disease"],
            "severity": prediction["severity"],
            "remedy": prediction["remedy"],
            "advice": prediction["advice"],
            "recommend_doctor_consultation": _should_recommend_doctor(prediction),
            "disclaimer": MEDICAL_DISCLAIMER,
        }
    )


@login_required
def prediction_history(request):
    predictions = DiseasePrediction.objects.filter(user=request.user).order_by("-created_at")

    data = [
        {
            "symptoms": p.symptoms,
            "disease": p.predicted_disease,
            "severity": p.severity,
            "date": p.created_at.strftime("%d %b %Y %H:%M"),
        }
        for p in predictions
    ]

    return JsonResponse(data, safe=False)


def get_symptoms(request):
    symptoms = [
        symptom.replace("symptom_", "").replace("_", " ").title()
        for symptom in SYMPTOM_COLUMNS
    ]

    return JsonResponse(symptoms, safe=False)
