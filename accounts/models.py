from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.email


class PremiumPlanPurchase(models.Model):
    PAYMENT_PENDING = "pending"
    PAYMENT_PAID = "paid"
    PAYMENT_FAILED = "failed"
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_FAILED, "Failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="premium_purchases")
    plan_code = models.CharField(max_length=50)
    plan_name = models.CharField(max_length=100)
    price_inr = models.PositiveIntegerField()
    sessions_included = models.PositiveIntegerField(default=1)
    sessions_used = models.PositiveIntegerField(default=0)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_PENDING,
    )
    payment_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def remaining_sessions(self):
        return max(self.sessions_included - self.sessions_used, 0)

    def __str__(self):
        return f"{self.user.email} - {self.plan_name}"


class DoctorConsultation(models.Model):
    MODE_GOOGLE_MEET = "google_meet"
    MODE_VIDEO_CALL = "video_call"
    MODE_CHOICES = [
        (MODE_GOOGLE_MEET, "Google Meet"),
        (MODE_VIDEO_CALL, "Video Call"),
    ]

    STATUS_REQUESTED = "requested"
    STATUS_SCHEDULED = "scheduled"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_REQUESTED, "Requested"),
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_COMPLETED, "Completed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="doctor_consultations")
    purchase = models.ForeignKey(
        PremiumPlanPurchase,
        on_delete=models.CASCADE,
        related_name="consultations",
    )
    patient_name = models.CharField(max_length=150)
    contact_email = models.EmailField()
    symptoms_summary = models.TextField()
    preferred_date = models.DateField(null=True, blank=True)
    consultation_mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    meeting_link = models.URLField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_REQUESTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} - {self.consultation_mode}"
