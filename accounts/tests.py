import json

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from .models import DoctorConsultation, PremiumPlanPurchase


@override_settings(DEFAULT_DOCTOR_MEET_LINK="https://meet.google.com/test-medcore-room")
class DoctorPlanFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="demo@example.com",
            email="demo@example.com",
            password="testpass123",
            first_name="Demo User",
        )
        self.client.login(username="demo@example.com", password="testpass123")

    def test_doctor_plan_listing_requires_login(self):
        self.client.logout()
        response = self.client.get("/accounts/doctor/plans/")
        self.assertEqual(response.status_code, 302)

    def test_cannot_book_without_active_plan(self):
        response = self.client.post(
            "/accounts/doctor/book/",
            data=json.dumps(
                {
                    "patient_name": "Demo User",
                    "contact_email": "demo@example.com",
                    "symptoms_summary": "High fever and chest pain",
                    "consultation_mode": "google_meet",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_activate_plan_and_book_consultation(self):
        activate_response = self.client.post(
            "/accounts/doctor/activate/",
            data=json.dumps({"plan_code": "doctor_once_500"}),
            content_type="application/json",
        )
        self.assertEqual(activate_response.status_code, 200)
        self.assertEqual(PremiumPlanPurchase.objects.count(), 1)

        book_response = self.client.post(
            "/accounts/doctor/book/",
            data=json.dumps(
                {
                    "patient_name": "Demo User",
                    "contact_email": "demo@example.com",
                    "symptoms_summary": "Persistent cough and fatigue",
                    "preferred_date": "2026-03-20",
                    "consultation_mode": "google_meet",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(book_response.status_code, 200)
        self.assertEqual(DoctorConsultation.objects.count(), 1)

        purchase = PremiumPlanPurchase.objects.get()
        consultation = DoctorConsultation.objects.get()

        self.assertEqual(purchase.sessions_used, 1)
        self.assertEqual(consultation.status, DoctorConsultation.STATUS_SCHEDULED)
        self.assertEqual(consultation.meeting_link, "https://meet.google.com/test-medcore-room")
