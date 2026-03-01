from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random
from .models import EmailOTP
from .utils import send_otp_email
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout



@login_required
def user_info(request):

    user = request.user

    return JsonResponse({
        "name": user.first_name or "User",
        "email": user.email
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

        otp = str(random.randint(100000, 999999))

        EmailOTP.objects.filter(email=email).delete()

        EmailOTP.objects.create(
            email=email,
            otp=otp
        )


        # ✅ Store user info in session
        request.session["otp_email"] = email
        request.session["otp_name"] = name
        request.session["otp_password"] = password

        sent = send_otp_email(email, otp)

        return JsonResponse({"success": sent})

    

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



