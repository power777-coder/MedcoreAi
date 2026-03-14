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
    path("login-user/", views.login_user, name="login_user"),
    path("firebase-login/", views.firebase_login),
    path("logout/", views.logout_user),
    path("doctor/plans/", views.doctor_plans, name="doctor_plans"),
    path("doctor/activate/", views.activate_doctor_plan, name="activate_doctor_plan"),
    path("doctor/book/", views.book_doctor_consultation, name="book_doctor_consultation"),
]
