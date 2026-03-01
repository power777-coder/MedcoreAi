from django.contrib import admin
from django.urls import path, include
from .views import home

urlpatterns = [
    path('', home, name='home'),   # 👈 THIS FIXES 404
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('predict/', include('prediction.urls')),
]
