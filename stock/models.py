from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Gestionnaire personnalisé pour le modèle CustomUser."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'adresse email est obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Modèle utilisateur personnalisé utilisant l'email comme identifiant."""
    username = None
    email = models.EmailField(_('adresse email'), unique=True)
    telephone = models.CharField(_('téléphone'), max_length=20, blank=True)
    adresse = models.TextField(_('adresse'), blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class Categorie(models.Model):
    """Modèle pour les catégories de produits."""
    nom = models.CharField(_('nom'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(_('date de mise à jour'), auto_now=True)

    class Meta:
        verbose_name = _('catégorie')
        verbose_name_plural = _('catégories')
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Fournisseur(models.Model):
    """Modèle pour les fournisseurs de produits."""
    nom = models.CharField(_('nom'), max_length=100)
    email = models.EmailField(_('adresse email'), unique=True)
    telephone = models.CharField(_('téléphone'), max_length=20)
    adresse = models.TextField(_('adresse'))
    contact = models.CharField(_('personne à contacter'), max_length=100, blank=True)
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(_('date de mise à jour'), auto_now=True)

    class Meta:
        verbose_name = _('fournisseur')
        verbose_name_plural = _('fournisseurs')
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.email})"


class Produit(models.Model):
    """Modèle pour les produits en stock."""
    code = models.CharField(_('code'), max_length=50, unique=True)
    designation = models.CharField(_('désignation'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('catégorie')
    )
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('fournisseur principal')
    )
    prix_achat = models.DecimalField(
        _('prix d\'achat'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    prix_vente = models.DecimalField(
        _('prix de vente'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    quantite_stock = models.PositiveIntegerField(_('quantité en stock'), default=0)
    seuil_alerte = models.PositiveIntegerField(_('seuil d\'alerte'), default=5)
    photo = models.ImageField(
        _('photo'),
        upload_to='produits/',
        null=True,
        blank=True
    )
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(_('date de mise à jour'), auto_now=True)

    class Meta:
        verbose_name = _('produit')
        verbose_name_plural = _('produits')
        ordering = ['designation']

    def __str__(self):
        return f"{self.designation} ({self.code})"

    @property
    def statut_stock(self):
        """Retourne le statut du stock (disponible, bientôt épuisé, épuisé)."""
        if self.quantite_stock == 0:
            return 'Épuisé'
        elif self.quantite_stock <= self.seuil_alerte:
            return 'Bientôt épuisé'
        return 'Disponible'


class EntreeStock(models.Model):
    """Modèle pour les entrées en stock."""
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        verbose_name=_('produit')
    )
    annulee = models.BooleanField(_('annulée'), default=False, help_text=_("Indique si cette entrée a été annulée"))
    quantite = models.PositiveIntegerField(_('quantité'))
    prix_unitaire = models.DecimalField(
        _('prix unitaire'),
        max_digits=10,
        decimal_places=2
    )
    date = models.DateTimeField(_('date d\'entrée'), auto_now_add=True)
    utilisateur = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('utilisateur')
    )
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('fournisseur')
    )
    reference = models.CharField(_('référence'), max_length=100, blank=True)
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        verbose_name = _('entrée en stock')
        verbose_name_plural = _('entrées en stock')
        ordering = ['-date']

    def save(self, *args, **kwargs):
        """Met à jour la quantité en stock du produit lors de la sauvegarde."""
        # Si c'est une nouvelle entrée
        if not self.pk:
            self.produit.quantite_stock += self.quantite
            self.produit.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Met à jour la quantité en stock du produit lors de la suppression."""
        self.produit.quantite_stock -= self.quantite
        self.produit.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Entrée de {self.quantite} {self.produit} le {self.date.strftime('%d/%m/%Y')}"


class SortieStock(models.Model):
    """Modèle pour les sorties de stock."""
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        verbose_name=_('produit')
    )
    quantite = models.PositiveIntegerField(_('quantité'))
    prix_unitaire = models.DecimalField(
        _('prix unitaire'),
        max_digits=10,
        decimal_places=2
    )
    date = models.DateTimeField(_('date de sortie'), auto_now_add=True)
    utilisateur = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('utilisateur')
    )
    client = models.CharField(_('client'), max_length=200, blank=True)
    reference = models.CharField(_('référence'), max_length=100, blank=True)
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        verbose_name = _('sortie de stock')
        verbose_name_plural = _('sorties de stock')
        ordering = ['-date']

    def save(self, *args, **kwargs):
        """Vérifie et met à jour la quantité en stock du produit lors de la sauvegarde."""
        # Vérifie si la quantité en stock est suffisante
        if self.produit.quantite_stock < self.quantite:
            raise ValueError("Stock insuffisant pour cette sortie.")
        
        # Si c'est une nouvelle sortie
        if not self.pk:
            self.produit.quantite_stock -= self.quantite
            self.produit.save()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Restaure la quantité en stock du produit lors de la suppression."""
        self.produit.quantite_stock += self.quantite
        self.produit.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Sortie de {self.quantite} {self.produit} le {self.date.strftime('%d/%m/%Y')}"


class Notification(models.Model):
    """Modèle pour les notifications du système."""
    class Niveau(models.TextChoices):
        INFO = 'info', _('Information')
        WARNING = 'warning', _('Avertissement')
        DANGER = 'danger', _('Danger')
    
    utilisateur = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('utilisateur')
    )
    message = models.TextField(_('message'))
    niveau = models.CharField(
        _('niveau'),
        max_length=10,
        choices=Niveau.choices,
        default=Niveau.INFO
    )
    vue = models.BooleanField(_('vue'), default=False)
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    lien = models.CharField(_('lien'), max_length=200, blank=True, null=True)
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
    
    def __str__(self):
        return f"{self.get_niveau_display()}: {self.message[:50]}..."
    
    def marquer_comme_vue(self):
        """Marque la notification comme vue."""
        self.vue = True
        self.save(update_fields=['vue'])
        return self
