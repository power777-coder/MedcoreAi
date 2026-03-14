from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_emailotp_created_at"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PremiumPlanPurchase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan_code", models.CharField(max_length=50)),
                ("plan_name", models.CharField(max_length=100)),
                ("price_inr", models.PositiveIntegerField()),
                ("sessions_included", models.PositiveIntegerField(default=1)),
                ("sessions_used", models.PositiveIntegerField(default=0)),
                (
                    "payment_status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("payment_reference", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="premium_purchases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DoctorConsultation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("patient_name", models.CharField(max_length=150)),
                ("contact_email", models.EmailField(max_length=254)),
                ("symptoms_summary", models.TextField()),
                ("preferred_date", models.DateField(blank=True, null=True)),
                (
                    "consultation_mode",
                    models.CharField(
                        choices=[("google_meet", "Google Meet"), ("video_call", "Video Call")],
                        max_length=20,
                    ),
                ),
                ("meeting_link", models.URLField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("requested", "Requested"), ("scheduled", "Scheduled"), ("completed", "Completed")],
                        default="requested",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "purchase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="consultations",
                        to="accounts.premiumplanpurchase",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="doctor_consultations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
