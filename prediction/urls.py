from django.urls import path

from .views import chat_predict, get_symptoms, predict_disease, prediction_history

urlpatterns = [
    path("predict/", predict_disease),
    path("chatbot/", chat_predict),
    path("history/", prediction_history),
    path("symptoms/", get_symptoms),
]
