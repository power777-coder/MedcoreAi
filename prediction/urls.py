from django.urls import path
from .views import predict_disease
from .views import prediction_history
from .views import get_symptoms

urlpatterns = [
    path("predict/", predict_disease),
    path("history/", prediction_history),
    path("symptoms/", get_symptoms),

]
