from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Categorie, Produit, MouvementStock


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'nombre_produits', 'date_creation')
    search_fields = ('nom', 'description')
    list_filter = ('date_creation',)
    readonly_fields = ('date_creation', 'date_modification')
    
    def nombre_produits(self, obj):
        return obj.produit_set.count()
    nombre_produits.short_description = _('Nombre de produits')


class MouvementStockInline(admin.TabularInline):
    model = MouvementStock
    extra = 0
    readonly_fields = ('type_mouvement', 'quantite', 'date_mouvement', 'utilisateur', 'notes')
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation', 'categorie', 'quantite_stock', 'seuil_alerte', 'unite', 'en_alerte', 'actif')
    list_filter = ('categorie', 'actif', 'unite')
    search_fields = ('code', 'designation', 'description')
    readonly_fields = ('date_creation', 'date_modification', 'en_alerte')
    list_editable = ('seuil_alerte', 'actif')
    list_per_page = 20
    inlines = [MouvementStockInline]
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('code', 'designation', 'description', 'categorie', 'unite')
        }),
        (_('Stock et prix'), {
            'fields': ('quantite_stock', 'seuil_alerte', 'prix_achat', 'prix_vente')
        }),
        (_('État et dates'), {
            'fields': ('actif', 'date_creation', 'date_modification', 'en_alerte')
        }),
    )
    
    def en_alerte(self, obj):
        return obj.quantite_stock <= obj.seuil_alerte
    en_alerte.boolean = True
    en_alerte.short_description = _('En alerte')


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('date_mouvement', 'produit', 'type_mouvement', 'quantite', 'utilisateur')
    list_filter = ('type_mouvement', 'date_mouvement')
    search_fields = ('produit__code', 'produit__designation', 'notes')
    readonly_fields = ('utilisateur', 'date_creation')
    date_hierarchy = 'date_mouvement'
    list_per_page = 20
    
    fieldsets = (
        (None, {
            'fields': ('produit', 'type_mouvement', 'quantite', 'date_mouvement')
        }),
        (_('Informations supplémentaires'), {
            'fields': ('utilisateur', 'notes', 'date_creation'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Nouvel enregistrement
            obj.utilisateur = request.user
        super().save_model(request, obj, form, change)
