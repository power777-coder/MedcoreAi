from django.shortcuts import render
from django.conf import settings

def home(request):
    return render(
        request,
        "index.html",
        {
            "firebase_config": settings.FIREBASE_WEB_CONFIG,
        },
    )
