from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Categorie(models.Model):
    """Catégorie pour classer les produits"""
    nom = models.CharField(_('nom'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('catégorie')
        verbose_name_plural = _('catégories')
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Produit(models.Model):
    """Produit en stock"""
    UNITE_CHOICES = [
        ('unite', _('Unité')),
        ('kg', _('Kilogramme')),
        ('g', _('Gramme')),
        ('l', _('Litre')),
        ('m', _('Mètre')),
        ('m2', _('Mètre carré')),
        ('m3', _('Mètre cube')),
    ]

    code = models.CharField(_('code'), max_length=50, unique=True)
    designation = models.CharField(_('désignation'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('catégorie')
    )
    quantite_stock = models.DecimalField(
        _('quantité en stock'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    seuil_alerte = models.DecimalField(
        _('seuil d\'alerte'),
        max_digits=10,
        decimal_places=2,
        default=5,
        help_text=_('Seuil en dessous duquel une alerte est déclenchée')
    )
    unite = models.CharField(
        _('unité de mesure'),
        max_length=10,
        choices=UNITE_CHOICES,
        default='unite'
    )
    prix_achat = models.DecimalField(
        _('prix d\'achat'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    prix_vente = models.DecimalField(
        _('prix de vente'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    actif = models.BooleanField(_('actif'), default=True)
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('produit')
        verbose_name_plural = _('produits')
        ordering = ['designation']

    def __str__(self):
        return f"{self.designation} ({self.code})"
    
    @property
    def en_alerte(self):
        """Vérifie si le stock est en dessous du seuil d'alerte"""
        return self.quantite_stock <= self.seuil_alerte


class MouvementStock(models.Model):
    """Mouvement d'entrée ou de sortie de stock"""
    TYPE_MOUVEMENT = [
        ('entree', _('Entrée en stock')),
        ('sortie', _('Sortie de stock')),
    ]

    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        verbose_name=_('produit'),
        related_name='mouvements'
    )
    type_mouvement = models.CharField(
        _('type de mouvement'),
        max_length=10,
        choices=TYPE_MOUVEMENT
    )
    quantite = models.DecimalField(
        _('quantité'),
        max_digits=10,
        decimal_places=2
    )
    date_mouvement = models.DateTimeField(
        _('date du mouvement'),
        default=timezone.now
    )
    utilisateur = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('utilisateur')
    )
    notes = models.TextField(_('notes'), blank=True)
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)

    class Meta:
        verbose_name = _('mouvement de stock')
        verbose_name_plural = _('mouvements de stock')
        ordering = ['-date_mouvement']

    def __str__(self):
        return f"{self.get_type_mouvement_display()} - {self.produit} - {self.quantite}"
    
    def save(self, *args, **kwargs):
        """Met à jour le stock du produit lors de la sauvegarde"""
        if not self.pk:  # Nouvel enregistrement
            if self.type_mouvement == 'entree':
                self.produit.quantite_stock += self.quantite
            else:  # sortie
                self.produit.quantite_stock -= self.quantite
            self.produit.save()
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Annule l'effet du mouvement sur le stock lors de la suppression"""
        if self.type_mouvement == 'entree':
            self.produit.quantite_stock -= self.quantite
        else:  # sortie
            self.produit.quantite_stock += self.quantite
        self.produit.save()
        super().delete(*args, **kwargs)
