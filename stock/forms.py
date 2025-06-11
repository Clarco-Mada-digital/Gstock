from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _

from .models import Categorie, Produit, Fournisseur, EntreeStock, SortieStock


class CustomUserCreationForm(UserCreationForm):
    """Formulaire de création d'utilisateur personnalisé."""
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'telephone', 'adresse')
        labels = {
            'email': _('Adresse email'),
            'first_name': _('Prénom'),
            'last_name': _('Nom'),
            'telephone': _('Téléphone'),
            'adresse': _('Adresse'),
        }


class CustomUserChangeForm(UserChangeForm):
    """Formulaire de modification d'utilisateur personnalisé."""
    class Meta(UserChangeForm.Meta):
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'telephone', 'adresse')
        labels = {
            'email': _('Adresse email'),
            'first_name': _('Prénom'),
            'last_name': _('Nom'),
            'telephone': _('Téléphone'),
            'adresse': _('Adresse'),
        }


class CategorieForm(forms.ModelForm):
    """Formulaire pour les catégories de produits."""
    class Meta:
        model = Categorie
        fields = ('nom', 'description')
        labels = {
            'nom': _('Nom de la catégorie'),
            'description': _('Description'),
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class FournisseurForm(forms.ModelForm):
    """Formulaire pour les fournisseurs."""
    class Meta:
        model = Fournisseur
        fields = ('nom', 'email', 'telephone', 'adresse', 'contact')
        labels = {
            'nom': _('Nom du fournisseur'),
            'email': _('Adresse email'),
            'telephone': _('Téléphone'),
            'adresse': _('Adresse complète'),
            'contact': _('Personne à contacter'),
        }
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class ProduitForm(forms.ModelForm):
    """Formulaire pour la création et la modification des produits."""
    
    # Ajout d'un champ personnalisé pour la suppression de la photo
    supprimer_photo = forms.BooleanField(
        required=False,
        label='Supprimer la photo actuelle',
        help_text='Cocher pour supprimer la photo actuelle du produit.'
    )
    
    class Meta:
        model = Produit
        fields = [
            'code', 'designation', 'description', 'categorie', 'fournisseur',
            'prix_achat', 'prix_vente', 'quantite_stock', 'seuil_alerte',
            'photo'
        ]
        labels = {
            'code': 'Code produit',
            'designation': 'Désignation',
            'description': 'Description',
            'categorie': 'Catégorie',
            'fournisseur': 'Fournisseur principal',
            'prix_achat': 'Prix d\'achat (€)',
            'prix_vente': 'Prix de vente (€)',
            'quantite_stock': 'Quantité en stock',
            'seuil_alerte': 'Seuil d\'alerte',
            'photo': 'Photo du produit'
        }
        help_texts = {
            'code': 'Code unique d\'identification du produit',
            'seuil_alerte': 'Seuil en dessous duquel une alerte de stock faible sera déclenchée',
        }
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-textarea mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Décrivez brièvement le produit...'
            }),
            'prix_achat': forms.NumberInput(attrs={
                'step': '0.01', 
                'min': '0',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': '0.00'
            }),
            'prix_vente': forms.NumberInput(attrs={
                'step': '0.01', 
                'min': '0',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': '0.00'
            }),
            'quantite_stock': forms.NumberInput(attrs={
                'min': '0',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': '0'
            }),
            'seuil_alerte': forms.NumberInput(attrs={
                'min': '0',
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': '5'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'ex: PROD-001'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Nom du produit'
            }),
            'categorie': forms.Select(attrs={
                'class': 'form-select mt-1 block w-full rounded-md border-gray-300 shadow-sm'
            }),
            'fournisseur': forms.Select(attrs={
                'class': 'form-select mt-1 block w-full rounded-md border-gray-300 shadow-sm'
            }),
            'unite_mesure': forms.Select(attrs={
                'class': 'form-select mt-1 block w-full rounded-md border-gray-300 shadow-sm'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
                'onchange': 'document.getElementById(\'file-name\').textContent = this.files[0] ? this.files[0].name : \'Aucun fichier sélectionné\''
            }),
            # Champ actif commenté car non présent dans le modèle
            # 'actif': forms.CheckboxInput(attrs={
            #     'class': 'form-checkbox h-5 w-5 text-blue-600 rounded'
            # }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnalisation des querysets
        self.fields['fournisseur'].queryset = Fournisseur.objects.all().order_by('nom')
        self.fields['categorie'].queryset = Categorie.objects.all().order_by('nom')
        
        # Ajout de classes pour les champs obligatoires
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' required-field'
        
        # Si on est en mode édition, on initialise le champ supprimer_photo
        if self.instance and self.instance.photo:
            self.fields['photo'].required = False
            self.fields['photo'].help_text = 'Laisser vide pour conserver la photo actuelle.'
        else:
            # Si c'est une création ou si pas de photo, on cache le champ de suppression
            self.fields.pop('supprimer_photo', None)
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code:
            raise forms.ValidationError("Le code produit est obligatoire.")
            
        # Vérification de l'unicité du code (sauf pour l'instance actuelle)
        qs = Produit.objects.filter(code__iexact=code)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            
        if qs.exists():
            raise forms.ValidationError("Ce code produit est déjà utilisé par un autre produit.")
            
        return code.upper()  # Convertir en majuscules
    
    def clean_prix_vente(self):
        prix_vente = self.cleaned_data.get('prix_vente')
        prix_achat = self.cleaned_data.get('prix_achat')
        
        if prix_vente is not None and prix_achat is not None and prix_vente < prix_achat:
            raise forms.ValidationError(
                "Le prix de vente ne peut pas être inférieur au prix d'achat."
            )
            
        return prix_vente
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérification cohérence seuil d'alerte
        quantite_stock = cleaned_data.get('quantite_stock')
        seuil_alerte = cleaned_data.get('seuil_alerte')
        
        if quantite_stock is not None and seuil_alerte is not None and quantite_stock < 0:
            self.add_error('quantite_stock', "La quantité en stock ne peut pas être négative.")
        
        # Gestion de la suppression de la photo
        if cleaned_data.get('supprimer_photo') and self.instance and self.instance.photo:
            self.instance.photo.delete(save=False)
            cleaned_data['photo'] = None
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Si une nouvelle photo est fournie, supprimer l'ancienne
        if 'photo' in self.changed_data and self.instance.photo:
            self.instance.photo.delete(save=False)
        
        if commit:
            instance.save()
            self.save_m2m()
            
        return instance


class EntreeStockForm(forms.ModelForm):
    """Formulaire pour les entrées en stock."""
    class Meta:
        model = EntreeStock
        fields = ('produit', 'quantite', 'prix_unitaire', 'fournisseur', 'reference', 'notes')
        labels = {
            'produit': _('Produit'),
            'quantite': _('Quantité'),
            'prix_unitaire': _('Prix unitaire (FCFA)'),
            'fournisseur': _('Fournisseur'),
            'reference': _('Référence (bon de livraison, facture, etc.)'),
            'notes': _('Notes supplémentaires'),
        }
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'prix_unitaire': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les produits actifs
        self.fields['produit'].queryset = Produit.objects.all().order_by('designation')
        self.fields['fournisseur'].queryset = Fournisseur.objects.all().order_by('nom')
        
        # Si l'utilisateur a des permissions limitées, filtrer les produits
        if user and not user.is_superuser:
            # Ici, vous pouvez ajouter une logique pour filtrer les produits
            # en fonction des permissions de l'utilisateur
            pass

    def clean_quantite(self):
        quantite = self.cleaned_data.get('quantite')
        if quantite <= 0:
            raise forms.ValidationError(_('La quantité doit être supérieure à zéro.'))
        return quantite


class SortieStockForm(forms.ModelForm):
    """Formulaire pour les sorties de stock."""
    class Meta:
        model = SortieStock
        fields = ('produit', 'quantite', 'prix_unitaire', 'client', 'reference', 'notes')
        labels = {
            'produit': _('Produit'),
            'quantite': _('Quantité'),
            'prix_unitaire': _('Prix unitaire (FCFA)'),
            'client': _('Client (nom ou entreprise)'),
            'reference': _('Référence (bon de sortie, facture, etc.)'),
            'notes': _('Notes supplémentaires'),
        }
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'prix_unitaire': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les produits avec stock disponible
        self.fields['produit'].queryset = Produit.objects.filter(quantite_stock__gt=0).order_by('designation')
        
        # Si l'utilisateur a des permissions limitées, filtrer les produits
        if user and not user.is_superuser:
            # Ici, vous pouvez ajouter une logique pour filtrer les produits
            # en fonction des permissions de l'utilisateur
            pass

    def clean_quantite(self):
        quantite = self.cleaned_data.get('quantite')
        produit = self.cleaned_data.get('produit')
        
        if quantite <= 0:
            raise forms.ValidationError(_('La quantité doit être supérieure à zéro.'))
            
        if produit and quantite > produit.quantite_stock:
            raise forms.ValidationError(
                _('Stock insuffisant. Quantité disponible: %(stock)s')
                % {'stock': produit.quantite_stock}
            )
            
        return quantite


class FiltreMouvementStockForm(forms.Form):
    """Formulaire de filtrage des mouvements de stock."""
    TYPE_MOUVEMENT = [
        ('', 'Tous les mouvements'),
        ('entree', 'Entrées en stock'),
        ('sortie', 'Sorties de stock'),
    ]
    
    type_mouvement = forms.ChoiceField(
        choices=TYPE_MOUVEMENT,
        required=False,
        label='Type de mouvement',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.all().order_by('designation'),
        required=False,
        label='Produit',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_debut = forms.DateField(
        required=False,
        label='Du',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_fin = forms.DateField(
        required=False,
        label='Au',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produit'].empty_label = 'Tous les produits'


class RapportMouvementsForm(forms.Form):
    """Formulaire pour les rapports de mouvements de stock."""
    date_debut = forms.DateField(
        label='Date de début',
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_fin = forms.DateField(
        label='Date de fin',
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.all().order_by('designation'),
        required=False,
        label='Produit spécifique',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin and date_debut > date_fin:
            raise forms.ValidationError("La date de début doit être antérieure à la date de fin.")
            
        return cleaned_data
