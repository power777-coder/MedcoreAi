from django.urls import path
from .views import sign_in
from .views import send_otp, verify_otp
from .views import user_info
from . import views

urlpatterns = [
    path("signin/", sign_in, name="signin"),
    path("send-otp/", send_otp),
    path("verify-otp/", verify_otp),
    path("user-info/", views.user_info),
]
