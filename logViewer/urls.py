from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logs/', include('robot_logs.urls')),
    path('', include('robot_logs.urls')),  # Redirection de la page d'accueil vers les logs
]
