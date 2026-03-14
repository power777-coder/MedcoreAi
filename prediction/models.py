

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class DiseasePrediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE , null=True, blank=True)
    symptoms = models.TextField()
    predicted_disease = models.CharField(max_length=200)
    severity = models.CharField(max_length=20)
    uploaded_image = models.FileField(upload_to="prediction_uploads/", null=True, blank=True)
    image_analysis = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
         return f"{self.predicted_disease} ({self.created_at})"
