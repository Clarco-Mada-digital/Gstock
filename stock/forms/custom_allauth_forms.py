from django import forms
from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class CustomSignupForm(SignupForm):
    """Formulaire d'inscription personnalisé pour Allauth."""
    first_name = forms.CharField(
        max_length=30,
        label=_('Prénom'),
        widget=forms.TextInput(attrs={'placeholder': _('Votre prénom')})
    )
    last_name = forms.CharField(
        max_length=30,
        label=_('Nom'),
        widget=forms.TextInput(attrs={'placeholder': _('Votre nom')})
    )
    telephone = forms.CharField(
        max_length=20,
        required=False,
        label=_('Téléphone'),
        widget=forms.TextInput(attrs={'placeholder': _('Votre numéro de téléphone')})
    )
    adresse = forms.CharField(
        max_length=255,
        required=False,
        label=_('Adresse'),
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': _('Votre adresse complète')})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprimer le champ username
        if 'username' in self.fields:
            del self.fields['username']
        # Déplacer les champs pour qu'ils apparaissent dans l'ordre souhaité
        field_order = ['email', 'first_name', 'last_name', 'telephone', 'adresse', 'password1', 'password2']
        self.order_fields(field_order)

    def save(self, request):
        # Appel de la méthode save() de la classe parente
        user = super().save(request)
        # Ajout des champs supplémentaires
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.telephone = self.cleaned_data.get('telephone')
        user.adresse = self.cleaned_data.get('adresse')
        user.save()
        return user

class CustomSocialSignupForm(SocialSignupForm):
    """Formulaire d'inscription sociale personnalisé pour Allauth."""
    first_name = forms.CharField(
        max_length=30,
        label=_('Prénom'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Votre prénom')})
    )
    last_name = forms.CharField(
        max_length=30,
        label=_('Nom'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Votre nom')})
    )
    telephone = forms.CharField(
        max_length=20,
        required=False,
        label=_('Téléphone'),
        widget=forms.TextInput(attrs={'placeholder': _('Votre numéro de téléphone')})
    )
    adresse = forms.CharField(
        max_length=255,
        required=False,
        label=_('Adresse'),
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': _('Votre adresse complète')})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprimer le champ username
        if 'username' in self.fields:
            del self.fields['username']
        # Déplacer les champs pour qu'ils apparaissent dans l'ordre souhaité
        field_order = ['email', 'first_name', 'last_name', 'telephone', 'adresse']
        self.order_fields(field_order)

    def save(self, request):
        # Appel de la méthode save() de la classe parente
        user = super().save(request)
        # Ajout des champs supplémentaires
        user.first_name = self.cleaned_data.get('first_name') or user.first_name
        user.last_name = self.cleaned_data.get('last_name') or user.last_name
        user.telephone = self.cleaned_data.get('telephone') or user.telephone
        user.adresse = self.cleaned_data.get('adresse') or user.adresse
        user.save()
        return user
