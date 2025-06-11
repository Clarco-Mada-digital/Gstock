from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    CustomUser, Categorie, Produit, Fournisseur, EntreeStock, SortieStock
)


# Configuration de l'administration pour CustomUser
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informations personnelles'), {'fields': ('first_name', 'last_name', 'telephone', 'adresse')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Dates importantes'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


# Configuration de l'administration pour Categorie
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'date_creation', 'date_mise_a_jour')
    search_fields = ('nom', 'description')
    prepopulated_fields = {}


# Configuration de l'administration pour Fournisseur
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'telephone', 'date_creation')
    search_fields = ('nom', 'email', 'contact')
    list_filter = ('date_creation',)


# Configuration de l'administration pour Produit
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('designation', 'code', 'categorie', 'prix_vente', 'quantite_stock', 'statut_stock')
    list_filter = ('categorie', 'fournisseur')
    search_fields = ('designation', 'code', 'description')
    list_editable = ('prix_vente', 'quantite_stock')
    readonly_fields = ('statut_stock', 'date_creation', 'date_mise_a_jour')
    fieldsets = (
        (None, {
            'fields': ('code', 'designation', 'description', 'categorie', 'fournisseur')
        }),
        (_('Prix et stock'), {
            'fields': ('prix_achat', 'prix_vente', 'quantite_stock', 'seuil_alerte', 'statut_stock')
        }),
        (_('Médias'), {
            'fields': ('photo',)
        }),
        (_('Métadonnées'), {
            'classes': ('collapse',),
            'fields': ('date_creation', 'date_mise_a_jour'),
        }),
    )


# Configuration de l'administration pour EntreeStock
class EntreeStockAdmin(admin.ModelAdmin):
    list_display = ('produit', 'quantite', 'prix_unitaire', 'date', 'utilisateur', 'fournisseur')
    list_filter = ('date', 'fournisseur')
    search_fields = ('produit__designation', 'reference', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('utilisateur', 'date')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une nouvelle entrée
            obj.utilisateur = request.user
        super().save_model(request, obj, form, change)


# Configuration de l'administration pour SortieStock
class SortieStockAdmin(admin.ModelAdmin):
    list_display = ('produit', 'quantite', 'prix_unitaire', 'date', 'utilisateur', 'client')
    list_filter = ('date', 'client')
    search_fields = ('produit__designation', 'client', 'reference', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('utilisateur', 'date')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une nouvelle sortie
            obj.utilisateur = request.user
        super().save_model(request, obj, form, change)


# Enregistrement des modèles avec leurs configurations personnalisées
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Categorie, CategorieAdmin)
admin.site.register(Fournisseur, FournisseurAdmin)
admin.site.register(Produit, ProduitAdmin)
admin.site.register(EntreeStock, EntreeStockAdmin)
admin.site.register(SortieStock, SortieStockAdmin)
