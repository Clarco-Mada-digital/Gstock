from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db import models
from django.db.models import Q, Sum, F, Value, CharField
from django.utils import timezone
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import csv
import io
from .models import Produit, Categorie, MouvementStock
from .forms import ProduitForm, MouvementStockForm, CustomUserCreationForm


@login_required
def accueil(request):
    """Vue pour la page d'accueil du tableau de bord"""
    # Statistiques de base
    total_produits = Produit.objects.count()
    produits_en_alerte = Produit.objects.filter(quantite_stock__lte=models.F('seuil_alerte')).count()
    
    # Derniers mouvements
    derniers_mouvements = MouvementStock.objects.select_related('produit').order_by('-date_mouvement')[:5]
    
    # Produits en alerte
    produits_alerte = Produit.objects.filter(
        quantite_stock__lte=models.F('seuil_alerte')
    ).order_by('quantite_stock')[:5]
    
    context = {
        'title': _('Tableau de bord'),
        'total_produits': total_produits,
        'produits_en_alerte': produits_en_alerte,
        'derniers_mouvements': derniers_mouvements,
        'produits_alerte': produits_alerte,
    }
    return render(request, 'inventaire/accueil.html', context)


@login_required
def liste_produits(request):
    """Liste des produits avec pagination et recherche"""
    query = request.GET.get('q', '')
    
    produits = Produit.objects.all().order_by('designation')
    
    if query:
        produits = produits.filter(
            Q(designation__icontains=query) |
            Q(code__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(produits, 20)  # 20 produits par page
    
    try:
        produits = paginator.page(page)
    except PageNotAnInteger:
        produits = paginator.page(1)
    except EmptyPage:
        produits = paginator.page(paginator.num_pages)
    
    context = {
        'title': _('Liste des produits'),
        'produits': produits,
        'query': query,
    }
    return render(request, 'inventaire/produits/liste.html', context)


@login_required
def detail_produit(request, pk):
    """Détail d'un produit avec son historique de mouvements"""
    produit = get_object_or_404(Produit, pk=pk)
    mouvements = MouvementStock.objects.filter(produit=produit).order_by('-date_mouvement')[:10]
    
    context = {
        'title': f"Détail - {produit.designation}",
        'produit': produit,
        'mouvements': mouvements,
    }
    return render(request, 'inventaire/produits/detail.html', context)


@login_required
def ajouter_produit(request):
    """Ajouter un nouveau produit"""
    if request.method == 'POST':
        form = ProduitForm(request.POST)
        if form.is_valid():
            produit = form.save()
            messages.success(request, _('Le produit a été ajouté avec succès.'))
            return redirect('inventaire:detail_produit', pk=produit.pk)
    else:
        form = ProduitForm()
    
    context = {
        'title': _('Ajouter un produit'),
        'form': form,
    }
    return render(request, 'inventaire/produits/form.html', context)


@login_required
def modifier_produit(request, pk):
    """Modifier un produit existant"""
    produit = get_object_or_404(Produit, pk=pk)
    
    if request.method == 'POST':
        form = ProduitForm(request.POST, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(request, _('Le produit a été modifié avec succès.'))
            return redirect('inventaire:detail_produit', pk=produit.pk)
    else:
        form = ProduitForm(instance=produit)
    
    context = {
        'title': _('Modifier le produit'),
        'form': form,
        'produit': produit,
    }
    return render(request, 'inventaire/produits/form.html', context)


@login_required
def supprimer_produit(request, pk):
    """Supprimer un produit"""
    produit = get_object_or_404(Produit, pk=pk)
    
    if request.method == 'POST':
        try:
            produit.delete()
            messages.success(request, _('Le produit a été supprimé avec succès.'))
            return redirect('inventaire:liste_produits')
        except Exception as e:
            messages.error(request, _(f'Une erreur est survenue lors de la suppression : {str(e)}'))
            return redirect('inventaire:detail_produit', pk=pk)
    
    context = {
        'title': _('Supprimer le produit'),
        'produit': produit,
    }
    return render(request, 'inventaire/produits/confirmer_suppression.html', context)


@login_required
def entree_stock(request):
    """Enregistrer une entrée en stock"""
    if request.method == 'POST':
        form = MouvementStockForm(request.POST)
        if form.is_valid():
            mouvement = form.save(commit=False)
            mouvement.type_mouvement = 'entree'
            mouvement.utilisateur = request.user
            mouvement.save()
            
            # Mise à jour du stock via la méthode save() du modèle
            messages.success(request, _('L\'entrée en stock a été enregistrée avec succès.'))
            return redirect('inventaire:detail_produit', pk=mouvement.produit.pk)
    else:
        form = MouvementStockForm()
    
    context = {
        'title': _('Entrée en stock'),
        'form': form,
        'type_mouvement': 'entree',
    }
    return render(request, 'inventaire/mouvements/form.html', context)


@login_required
def sortie_stock(request):
    """Enregistrer une sortie de stock"""
    if request.method == 'POST':
        form = MouvementStockForm(request.POST)
        if form.is_valid():
            mouvement = form.save(commit=False)
            mouvement.type_mouvement = 'sortie'
            mouvement.utilisateur = request.user
            
            # Vérifier que le stock est suffisant
            if mouvement.quantite > mouvement.produit.quantite_stock:
                messages.error(request, _('La quantité en stock est insuffisante.'))
            else:
                mouvement.save()
                messages.success(request, _('La sortie de stock a été enregistrée avec succès.'))
                return redirect('inventaire:detail_produit', pk=mouvement.produit.pk)
    else:
        form = MouvementStockForm()
    
    context = {
        'title': _('Sortie de stock'),
        'form': form,
        'type_mouvement': 'sortie',
    }
    return render(request, 'inventaire/mouvements/form.html', context)


@login_required
def historique(request):
    """Historique des mouvements de stock"""
    # Récupérer les paramètres de filtrage
    produit_id = request.GET.get('produit')
    type_mouvement = request.GET.get('type_mouvement')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    # Construire la requête de base
    mouvements = MouvementStock.objects.select_related('produit', 'utilisateur').order_by('-date_mouvement')
    
    # Appliquer les filtres
    if produit_id:
        mouvements = mouvements.filter(produit_id=produit_id)
    
    if type_mouvement:
        mouvements = mouvements.filter(type_mouvement=type_mouvement)
    
    if date_debut:
        mouvements = mouvements.filter(date_mouvement__date__gte=date_debut)
    
    if date_fin:
        # Ajouter un jour pour inclure toute la journée de fin
        date_fin_obj = timezone.datetime.strptime(date_fin, '%Y-%m-%d')
        date_fin_obj = date_fin_obj + timezone.timedelta(days=1)
        mouvements = mouvements.filter(date_mouvement__date__lt=date_fin_obj)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(mouvements, 25)  # 25 éléments par page
    
    try:
        mouvements_pagines = paginator.page(page)
    except PageNotAnInteger:
        mouvements_pagines = paginator.page(1)
    except EmptyPage:
        mouvements_pagines = paginator.page(paginator.num_pages)
    
    # Préparer le contexte
    context = {
        'mouvements': mouvements_pagines,
        'produits': Produit.objects.all().order_by('designation'),
        'filtres_actifs': any([produit_id, type_mouvement, date_debut, date_fin]),
    }
    
    return render(request, 'inventaire/historique.html', context)


def signup(request):
    """Vue pour l'inscription des nouveaux utilisateurs"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Connecter automatiquement l'utilisateur après l'inscription
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.email, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, _('Inscription réussie ! Bienvenue sur Gestion de Stock.'))
                return redirect('inventaire:accueil')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'title': _("S'inscrire"),
        'form': form,
    }
    return render(request, 'registration/signup.html', context)


@login_required
def exporter_historique(request):
    """Exporter l'historique des mouvements au format CSV"""
    # Récupérer les mêmes filtres que pour la vue historique
    produit_id = request.GET.get('produit')
    type_mouvement = request.GET.get('type_mouvement')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    # Construire la requête de base
    mouvements = MouvementStock.objects.select_related('produit', 'utilisateur').order_by('-date_mouvement')
    
    # Appliquer les mêmes filtres
    if produit_id:
        mouvements = mouvements.filter(produit_id=produit_id)
    if type_mouvement:
        mouvements = mouvements.filter(type_mouvement=type_mouvement)
    if date_debut:
        mouvements = mouvements.filter(date_mouvement__date__gte=date_debut)
    if date_fin:
        date_fin_obj = timezone.datetime.strptime(date_fin, '%Y-%m-%d')
        date_fin_obj = date_fin_obj + timezone.timedelta(days=1)
        mouvements = mouvements.filter(date_mouvement__date__lt=date_fin_obj)
    
    # Créer un fichier CSV en mémoire
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="historique_mouvements.csv"'
    
    # Utiliser un writer CSV avec l'encodage UTF-8 et le délimiteur point-virgule
    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    # Écrire l'en-tête
    writer.writerow([
        'Date et heure',
        'Type de mouvement',
        'Référence produit',
        'Désignation',
        'Quantité',
        'Unité',
        'Utilisateur',
        'Notes'
    ])
    
    # Écrire les données
    for mouvement in mouvements:
        writer.writerow([
            timezone.localtime(mouvement.date_mouvement).strftime('%d/%m/%Y %H:%M'),
            'Entrée' if mouvement.type_mouvement == 'entree' else 'Sortie',
            mouvement.produit.code if mouvement.produit.code else '',
            mouvement.produit.designation,
            str(mouvement.quantite).replace('.', ','),  # Format français pour les nombres
            mouvement.produit.unite,
            mouvement.utilisateur.get_full_name() or mouvement.utilisateur.username,
            mouvement.notes or ''
        ])
    
    return response
