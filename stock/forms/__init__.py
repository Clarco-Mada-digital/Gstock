# Import des formulaires principaux
from .base_forms import (
    CustomUserCreationForm, CustomUserChangeForm,
    CategorieForm, FournisseurForm, ProduitForm,
    EntreeStockForm, SortieStockForm, FiltreMouvementStockForm,
    RapportMouvementsForm
)

# Import des formulaires personnalisés Allauth
from .custom_allauth_forms import CustomSignupForm, CustomSocialSignupForm

# Pour la rétrocompatibilité avec les imports existants
__all__ = [
    'CustomUserCreationForm', 'CustomUserChangeForm',
    'CategorieForm', 'FournisseurForm', 'ProduitForm',
    'EntreeStockForm', 'SortieStockForm', 'FiltreMouvementStockForm',
    'RapportMouvementsForm', 'CustomSignupForm', 'CustomSocialSignupForm'
]
