from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Produit, MouvementStock


class ProduitForm(forms.ModelForm):
    """Formulaire pour l'ajout et la modification de produits"""
    class Meta:
        model = Produit
        fields = [
            'code', 'designation', 'description', 'categorie',
            'quantite_stock', 'seuil_alerte', 'unite',
            'prix_achat', 'prix_vente', 'actif'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajout de classes Bootstrap aux champs
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        # Masquer le champ quantité stock si c'est une modification
        if self.instance and self.instance.pk:
            self.fields['quantite_stock'].widget = forms.HiddenInput()


class MouvementStockForm(forms.ModelForm):
    """Formulaire pour les entrées et sorties de stock"""
    class Meta:
        model = MouvementStock
        fields = ['produit', 'quantite', 'date_mouvement', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
            'date_mouvement': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                },
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajout de classes Bootstrap aux champs
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Limiter la liste des produits à ceux qui sont actifs
        self.fields['produit'].queryset = Produit.objects.filter(actif=True)
        
        # Rendre le champ produit plus convivial
        self.fields['produit'].label_from_instance = lambda obj: f"{obj.designation} ({obj.code}) - Stock: {obj.quantite_stock} {obj.unite}"
        
        # Définir la date du mouvement par défaut à maintenant
        if 'date_mouvement' not in self.initial:
            self.initial['date_mouvement'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean_quantite(self):
        """Valider que la quantité est positive"""
        quantite = self.cleaned_data.get('quantite')
        if quantite <= 0:
            raise forms.ValidationError(_('La quantité doit être supérieure à zéro.'))
        return quantite


class CustomUserCreationForm(UserCreationForm):
    """Formulaire d'inscription personnalisé basé sur l'email"""
    email = forms.EmailField(
        label=_('Adresse email'),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'})
    )
    password1 = forms.CharField(
        label=_('Mot de passe'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        help_text=_(
            'Votre mot de passe doit contenir au moins 8 caractères et ne pas être trop courant.'
        ),
    )
    password2 = forms.CharField(
        label=_('Confirmation du mot de passe'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        strip=False,
        help_text=_('Entrez le même mot de passe que précédemment, pour vérification.'),
    )

    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir l'ordre des champs
        self.order_fields(['email', 'first_name', 'last_name', 'password1', 'password2'])
        
        # Ajouter des placeholders et des libellés
        self.fields['first_name'].label = _('Prénom')
        self.fields['last_name'].label = _('Nom')
        self.fields['email'].widget.attrs.update({'placeholder': _('votre@email.com')})
        self.fields['first_name'].widget.attrs.update({'placeholder': _('Votre prénom')})
        self.fields['last_name'].widget.attrs.update({'placeholder': _('Votre nom')})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Cette adresse email est déjà utilisée.'))
        return email
