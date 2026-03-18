from django.urls import path
from . import views

urlpatterns = [
    path("predict/", views.predict_disease),
    path("history/", views.prediction_history),
    path("symptoms/", views.get_symptoms),
    path("chat/", views.chat_predict),
]
