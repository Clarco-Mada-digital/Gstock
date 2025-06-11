from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

# Import des vues depuis le module views
from . import views, api
from .views import (
    ProduitListView, ProduitDetailView, ProduitCreateView, ProduitUpdateView,
    CategorieListView, CategorieCreateView, CategorieUpdateView,
    FournisseurListView, FournisseurDetailView, FournisseurCreateView, FournisseurUpdateView,
    EntreeStockCreateView, EntreeStockDetailView, EntreeStockUpdateView, SortieStockCreateView, SortieStockDetailView,
    supprimer_produit, supprimer_categorie, supprimer_fournisseur, 
    annuler_entree, annuler_sortie,
    ListeEntreesView, ListeSortiesView,
    NotificationListView, NotificationMarkAsReadView, NotificationMarkAllAsReadView, NotificationCountView,
)
from .views.profil import ProfileView
from .views.historique import HistoriqueMouvementsView

app_name = 'stock'

urlpatterns = [
    # Page d'accueil
    path('', views.accueil, name='accueil'),
    
    # Authentification
    path('connexion/', auth_views.LoginView.as_view(template_name='stock/connexion.html'), 
         name='connexion'),
    path('deconnexion/', auth_views.LogoutView.as_view(next_page='stock:accueil'), 
         name='deconnexion'),
    
    # Produits
    path('produits/', ProduitListView.as_view(), name='liste_produits'),
    path('produits/ajouter/', ProduitCreateView.as_view(), name='ajouter_produit'),
    path('produits/<int:pk>/', ProduitDetailView.as_view(), name='detail_produit'),
    path('produits/<int:pk>/modifier/', ProduitUpdateView.as_view(), name='modifier_produit'),
    path('produits/<int:pk>/supprimer/', supprimer_produit, name='supprimer_produit'),
    
    # Catégories
    path('categories/', CategorieListView.as_view(), name='liste_categories'),
    path('categories/ajouter/', CategorieCreateView.as_view(), name='ajouter_categorie'),
    path('categories/<int:pk>/modifier/', CategorieUpdateView.as_view(), name='modifier_categorie'),
    path('categories/<int:pk>/supprimer/', supprimer_categorie, name='supprimer_categorie'),
    
    # Fournisseurs
    path('fournisseurs/', FournisseurListView.as_view(), name='liste_fournisseurs'),
    path('fournisseurs/ajouter/', FournisseurCreateView.as_view(), name='ajouter_fournisseur'),
    path('fournisseurs/<int:pk>/', FournisseurDetailView.as_view(), name='detail_fournisseur'),
    path('fournisseurs/<int:pk>/modifier/', FournisseurUpdateView.as_view(), name='modifier_fournisseur'),
    path('fournisseurs/<int:pk>/supprimer/', supprimer_fournisseur, name='supprimer_fournisseur'),
    
    # Mouvements de stock - Entrées
    path('entrees/', ListeEntreesView.as_view(), name='liste_entrees'),
    path('entrees/ajouter/', EntreeStockCreateView.as_view(), name='ajouter_entree'),
    path('entrees/<int:pk>/', EntreeStockDetailView.as_view(), name='detail_entree'),
    path('entrees/<int:pk>/modifier/', EntreeStockUpdateView.as_view(), name='modifier_entree'),
    path('entrees/<int:pk>/annuler/', annuler_entree, name='annuler_entree'),
    
    # Mouvements de stock - Sorties
    path('sorties/', ListeSortiesView.as_view(), name='liste_sorties'),
    path('sorties/ajouter/', SortieStockCreateView.as_view(), name='ajouter_sortie'),
    path('sorties/<int:pk>/', SortieStockDetailView.as_view(), name='detail_sortie'),
    path('sorties/<int:pk>/annuler/', annuler_sortie, name='annuler_sortie'),
    
    # API
    path('api/produits/<int:produit_id>/', api.get_produit_details, name='api_produit_details'),
    
    # Notifications
    path('notifications/', NotificationListView.as_view(), name='liste_notifications'),
    path('notifications/marquer-toutes-lues/', NotificationMarkAllAsReadView.as_view(), name='marquer_toutes_notifications_lues'),
    path('notifications/<int:pk>/marquer-lue/', NotificationMarkAsReadView.as_view(), name='marquer_notification_lue'),
    path('api/notifications/count/', NotificationCountView.as_view(), name='api_notification_count'),
    
    # Profil utilisateur
    path('profil/', ProfileView.as_view(), name='profil'),
    
    # Tableau de bord et rapports
    path('tableau-de-bord/', views.accueil, name='tableau_de_bord'),
    path('historique/', HistoriqueMouvementsView.as_view(), name='historique'),
    path('rapports/stock-faible/', views.rapport_stock_faible, name='rapport_stock_faible'),
    path('rapports/mouvements/', views.rapport_mouvements, name='rapport_mouvements'),
    path('rapports/', TemplateView.as_view(template_name='stock/rapports/accueil.html'), name='rapports'),
]
