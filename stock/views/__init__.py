# Import des vues de base
from .produits import (
    ProduitListView, ProduitDetailView, ProduitCreateView,
    ProduitUpdateView, supprimer_produit
)
from .fournisseurs import (
    FournisseurListView, FournisseurDetailView, FournisseurCreateView,
    FournisseurUpdateView, supprimer_fournisseur
)
from .categories import (
    CategorieListView, CategorieCreateView,
    CategorieUpdateView, supprimer_categorie
)
from .mouvements import (
    ListeEntreesView, EntreeStockCreateView, EntreeStockDetailView, EntreeStockUpdateView,
    ListeSortiesView, SortieStockCreateView, SortieStockDetailView,
    annuler_entree, annuler_sortie
)
from .rapports import (
    rapport_stock_faible, rapport_mouvements,
    generer_pdf_rapport_stock_faible, generer_excel_rapport_stock_faible
)
from .notifications import (
    NotificationListView, NotificationMarkAsReadView,
    NotificationMarkAllAsReadView, NotificationCountView
)
from .accueil import accueil

# Rendre les vues disponibles lors de l'import de stock.views
__all__ = [
    # Produits
    'ProduitListView', 'ProduitDetailView', 'ProduitCreateView',
    'ProduitUpdateView', 'supprimer_produit',
    
    # Fournisseurs
    'FournisseurListView', 'FournisseurDetailView', 'FournisseurCreateView',
    'FournisseurUpdateView', 'supprimer_fournisseur',
    
    # Catégories
    'CategorieListView', 'CategorieCreateView',
    'CategorieUpdateView', 'supprimer_categorie',
    
    # Mouvements
    'ListeEntreesView', 'EntreeStockCreateView', 'EntreeStockDetailView', 'EntreeStockUpdateView',
    'ListeSortiesView', 'SortieStockCreateView', 'SortieStockDetailView',
    'annuler_entree', 'annuler_sortie',
    
    # Rapports
    'rapport_stock_faible', 'rapport_mouvements',
    'generer_pdf_rapport_stock_faible', 'generer_excel_rapport_stock_faible',
    
    # Notifications
    'NotificationListView', 'NotificationMarkAsReadView',
    'NotificationMarkAllAsReadView', 'NotificationCountView',
    
    # Accueil
    'accueil',
]
