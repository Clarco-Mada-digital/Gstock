from django.urls import path
from . import views

app_name = 'inventaire'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('produits/', views.liste_produits, name='liste_produits'),
    path('produit/ajouter/', views.ajouter_produit, name='ajouter_produit'),
    path('produit/<int:pk>/', views.detail_produit, name='detail_produit'),
    path('produit/<int:pk>/modifier/', views.modifier_produit, name='modifier_produit'),
    path('produit/<int:pk>/supprimer/', views.supprimer_produit, name='supprimer_produit'),
    path('entree-stock/', views.entree_stock, name='entree_stock'),
    path('sortie-stock/', views.sortie_stock, name='sortie_stock'),
    path('historique/', views.historique, name='historique'),
    path('historique/exporter/', views.exporter_historique, name='exporter_historique'),
]
