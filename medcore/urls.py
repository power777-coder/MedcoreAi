from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),

    # Your custom app
    path('accounts/', include('accounts.urls')),

    # Allauth routes (DIFFERENT PREFIX)

    path('predict/', include('prediction.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
