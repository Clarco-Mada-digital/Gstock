"""
URL configuration for Gestion de Stock.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # URL de l'administration Django
    path('admin/', admin.site.urls),
    
    # URL de l'application inventaire
    path('', include('inventaire.urls', namespace='inventaire')),
    
    # URLs de l'application stock
    path('', include('stock.urls', namespace='stock')),
    
    # URLs d'authentification Allauth
    path('accounts/', include('allauth.urls')),
    
    # Redirection de la racine vers l'accueil
    path('', RedirectView.as_view(url='/', permanent=True)),
]

# URLs pour les fichiers média et statiques en mode développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
