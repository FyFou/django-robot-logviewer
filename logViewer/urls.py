from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logs/', include('robot_logs.urls')),
    # Remplacer la double inclusion par une redirection
    path('', RedirectView.as_view(url='logs/', permanent=True)),
]

# Ajouter les URLs pour servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
