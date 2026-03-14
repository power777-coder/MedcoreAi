from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
import json
import random
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from .models import DoctorConsultation, EmailOTP, PremiumPlanPurchase
from .utils import send_otp_email

DOCTOR_PREMIUM_PLANS = [
    {
        "code": "doctor_once_500",
        "name": "Doctor Connect Once",
        "price_inr": 500,
        "sessions_included": 1,
        "description": "One paid consultation with doctor follow-up and video-call access.",
    },
    {
        "code": "doctor_priority_1200",
        "name": "Priority Care Pack",
        "price_inr": 1200,
        "sessions_included": 3,
        "description": "Three doctor consultations for repeated review or follow-up care.",
    },
]


def _get_plan_by_code(plan_code):
    for plan in DOCTOR_PREMIUM_PLANS:
        if plan["code"] == plan_code:
            return plan
    return None


def _get_active_purchase(user):
    return (
        PremiumPlanPurchase.objects.filter(
            user=user,
            payment_status=PremiumPlanPurchase.PAYMENT_PAID,
            sessions_used__lt=F("sessions_included"),
        )
        .order_by("-created_at")
        .first()
    )


def _serialize_purchase(purchase):
    if not purchase:
        return None

    return {
        "id": purchase.id,
        "plan_name": purchase.plan_name,
        "price_inr": purchase.price_inr,
        "sessions_included": purchase.sessions_included,
        "sessions_used": purchase.sessions_used,
        "remaining_sessions": purchase.remaining_sessions,
        "payment_status": purchase.payment_status,
        "payment_reference": purchase.payment_reference,
    }


def _serialize_consultation(consultation):
    return {
        "id": consultation.id,
        "patient_name": consultation.patient_name,
        "contact_email": consultation.contact_email,
        "symptoms_summary": consultation.symptoms_summary,
        "preferred_date": consultation.preferred_date.isoformat() if consultation.preferred_date else "",
        "consultation_mode": consultation.consultation_mode,
        "meeting_link": consultation.meeting_link,
        "status": consultation.status,
        "created_at": consultation.created_at.strftime("%d %b %Y %H:%M"),
    }

def logout_user(request):
    logout(request)
    return JsonResponse({"success": True})

@login_required
def user_info(request):

    user = request.user

    return JsonResponse({
        "name": user.first_name or "User",
        "email": user.email
    })


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)

        email = data.get("email")
        password = data.get("password")

        user = authenticate(username=email, password=password)

        if user:
            login(request, user)
            return JsonResponse({"success": True})

        return JsonResponse({
            "success": False,
            "message": "Invalid credentials"
        })

@csrf_exempt
def sign_in(request):
    if request.method == "POST":
        data = json.loads(request.body)

        email = data.get("email")
        password = data.get("password")
        name = data.get("name")

        # create user if not exists
        user, created = User.objects.get_or_create(
            username=email,
            defaults={"email": email, "first_name": name}
        )

        if created:
            user.set_password(password)
            user.save()

        user = authenticate(username=email, password=password)
        if user:
            login(request, user)
            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": "Invalid credentials"})

@csrf_exempt
def send_otp(request):

    if request.method == "POST":

        data = json.loads(request.body)

        email = data.get("email")
        name = data.get("name")
        password = data.get("password")

        request.session["otp_email"] = email
        request.session["otp_name"] = name
        request.session["otp_password"] = password

        otp = str(random.randint(100000, 999999))

        EmailOTP.objects.update_or_create(
            email=email,
            defaults={"otp": otp}
        )

        sent = send_otp_email(email, otp)

        return JsonResponse({
            "success": sent,
            "existing_user": User.objects.filter(username=email).exists()
        })

    

def verify_otp(request):

    data = json.loads(request.body)

    email = request.session.get("otp_email")
    name = request.session.get("otp_name")
    password = request.session.get("otp_password")
    otp = data.get("otp")

    try:
        otp_obj = EmailOTP.objects.get(email=email)

        if timezone.now() - otp_obj.created_at > timedelta(minutes=5):
            return JsonResponse({
                "success": False,
                "expired": True,
                "message": "OTP expired"
            })

        if otp_obj.otp != otp:
            return JsonResponse({
                "success": False,
                "message": "Invalid OTP"
            })

    except EmailOTP.DoesNotExist:
        return JsonResponse({"success": False})

    # Create or update user
    user, created = User.objects.get_or_create(
        username=email,
        defaults={"email": email}
    )

    # ⭐ Always update password + name
    user.set_password(password)
    user.first_name = name or "User"
    user.save()

    # Authenticate
    user = authenticate(username=email, password=password)

    if user is None:
        return JsonResponse({
            "success": False,
            "message": "Authentication failed"
        })

    login(request, user)

    otp_obj.delete()

    return JsonResponse({"success": True})


@csrf_exempt
def firebase_login(request):
    print("Firebase login request received")

    if request.method == "POST":

        data = json.loads(request.body)

        email = data.get("email")
        name = data.get("name")

        if not email:
            return JsonResponse({"success": False})

        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                "email": email,
                "first_name": name or "User"
            }
        )

        login(request, user)

        return JsonResponse({"success": True})


@login_required
@require_GET
def doctor_plans(request):
    active_purchase = _get_active_purchase(request.user)
    consultations = DoctorConsultation.objects.filter(user=request.user).order_by("-created_at")[:5]

    return JsonResponse(
        {
            "plans": DOCTOR_PREMIUM_PLANS,
            "active_purchase": _serialize_purchase(active_purchase),
            "consultations": [_serialize_consultation(item) for item in consultations],
            "google_meet_enabled": bool(getattr(settings, "DEFAULT_DOCTOR_MEET_LINK", "")),
        }
    )


@csrf_exempt
@login_required
def activate_doctor_plan(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST request required"}, status=405)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    plan = _get_plan_by_code(data.get("plan_code"))
    if not plan:
        return JsonResponse({"success": False, "message": "Selected plan was not found."}, status=404)

    purchase = PremiumPlanPurchase.objects.create(
        user=request.user,
        plan_code=plan["code"],
        plan_name=plan["name"],
        price_inr=plan["price_inr"],
        sessions_included=plan["sessions_included"],
        payment_status=PremiumPlanPurchase.PAYMENT_PAID,
        payment_reference=f"MED-{timezone.now().strftime('%Y%m%d%H%M%S')}-{request.user.id}",
    )

    return JsonResponse(
        {
            "success": True,
            "message": f"{plan['name']} activated successfully.",
            "purchase": _serialize_purchase(purchase),
            "note": "This is a direct activation flow. Connect Razorpay or another payment gateway before production use.",
        }
    )


@csrf_exempt
@login_required
def book_doctor_consultation(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST request required"}, status=405)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    purchase = _get_active_purchase(request.user)
    if not purchase:
        return JsonResponse(
            {
                "success": False,
                "message": "You need an active premium doctor plan before booking a consultation.",
            },
            status=403,
        )

    patient_name = str(data.get("patient_name", request.user.first_name or "User")).strip()
    contact_email = str(data.get("contact_email", request.user.email)).strip()
    symptoms_summary = str(data.get("symptoms_summary", "")).strip()
    preferred_date_raw = str(data.get("preferred_date", "")).strip()
    consultation_mode = str(data.get("consultation_mode", DoctorConsultation.MODE_GOOGLE_MEET)).strip()

    if not symptoms_summary:
        return JsonResponse({"success": False, "message": "Symptoms or concern summary is required."}, status=400)

    if consultation_mode not in dict(DoctorConsultation.MODE_CHOICES):
        return JsonResponse({"success": False, "message": "Invalid consultation mode."}, status=400)

    preferred_date = None
    if preferred_date_raw:
        try:
            preferred_date = datetime.strptime(preferred_date_raw, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"success": False, "message": "Preferred date must be YYYY-MM-DD."}, status=400)

    meeting_link = ""
    status = DoctorConsultation.STATUS_REQUESTED
    if consultation_mode == DoctorConsultation.MODE_GOOGLE_MEET:
        meeting_link = getattr(settings, "DEFAULT_DOCTOR_MEET_LINK", "")
        if meeting_link:
            status = DoctorConsultation.STATUS_SCHEDULED

    consultation = DoctorConsultation.objects.create(
        user=request.user,
        purchase=purchase,
        patient_name=patient_name,
        contact_email=contact_email,
        symptoms_summary=symptoms_summary,
        preferred_date=preferred_date,
        consultation_mode=consultation_mode,
        meeting_link=meeting_link,
        status=status,
    )

    purchase.sessions_used += 1
    purchase.save(update_fields=["sessions_used"])

    return JsonResponse(
        {
            "success": True,
            "message": "Doctor consultation booked successfully.",
            "consultation": _serialize_consultation(consultation),
            "purchase": _serialize_purchase(purchase),
        }
    )


