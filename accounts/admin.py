from django.contrib import admin

from .models import DoctorConsultation, EmailOTP, PremiumPlanPurchase


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at")


@admin.register(PremiumPlanPurchase)
class PremiumPlanPurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan_name",
        "price_inr",
        "sessions_included",
        "sessions_used",
        "payment_status",
        "created_at",
    )
    list_filter = ("payment_status", "plan_code")
    search_fields = ("user__username", "user__email", "payment_reference")


@admin.register(DoctorConsultation)
class DoctorConsultationAdmin(admin.ModelAdmin):
    list_display = (
        "patient_name",
        "contact_email",
        "consultation_mode",
        "status",
        "preferred_date",
        "created_at",
    )
    list_filter = ("consultation_mode", "status")
    search_fields = ("patient_name", "contact_email", "user__username")
