from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, Q, Count, Case, When, Value, IntegerField, Prefetch, DecimalField, ExpressionWrapper
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models.functions import TruncDay, Coalesce, Concat, TruncMonth, ExtractMonth, ExtractYear
from django.http import JsonResponse, HttpResponse, HttpRequest, HttpResponseRedirect
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncDate

from .models import Produit, Categorie, Fournisseur, EntreeStock, SortieStock
from .forms import ProduitForm, CategorieForm, FournisseurForm, EntreeStockForm, SortieStockForm, CustomUserCreationForm


# Vues pour la page d'accueil et le tableau de bord
@login_required
def accueil(request):
    """Vue pour la page d'accueil du tableau de bord."""
    # Statistiques de base
    total_produits = Produit.objects.count()
    total_categories = Categorie.objects.count()
    total_fournisseurs = Fournisseur.objects.count()
    
    # Produits en alerte de stock
    produits_alerte = Produit.objects.filter(quantite_stock__lte=F('seuil_alerte'))
    
    # Derniers mouvements de stock
    dernieres_entrees = EntreeStock.objects.select_related('produit', 'fournisseur') \
        .order_by('-date')[:5]
    dernieres_sorties = SortieStock.objects.select_related('produit') \
        .order_by('-date')[:5]
    
    context = {
        'total_produits': total_produits,
        'total_categories': total_categories,
        'total_fournisseurs': total_fournisseurs,
        'produits_alerte': produits_alerte,
        'dernieres_entrees': dernieres_entrees,
        'dernieres_sorties': dernieres_sorties,
    }
    
    return render(request, 'stock/accueil.html', context)


# Vues pour les catégories
class CategorieListView(LoginRequiredMixin, ListView):
    model = Categorie
    template_name = 'stock/categorie_liste.html'
    context_object_name = 'categories'
    paginate_by = 10


class CategorieCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Categorie
    form_class = CategorieForm
    template_name = 'stock/categorie_form.html'
    success_url = reverse_lazy('stock:liste_categories')
    permission_required = 'stock.add_categorie'
    
    def form_valid(self, form):
        messages.success(self.request, _('Catégorie créée avec succès.'))
        return super().form_valid(form)


class CategorieUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Categorie
    form_class = CategorieForm
    template_name = 'stock/categorie_form.html'
    success_url = reverse_lazy('stock:liste_categories')
    permission_required = 'stock.change_categorie'
    
    def form_valid(self, form):
        messages.success(self.request, _('Catégorie mise à jour avec succès.'))
        return super().form_valid(form)


@login_required
@permission_required('stock.delete_categorie', raise_exception=True)
def supprimer_categorie(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        if not Produit.objects.filter(categorie=categorie).exists():
            categorie.delete()
            messages.success(request, _('Catégorie supprimée avec succès.'))
            return redirect('stock:liste_categories')
        else:
            messages.error(
                request, 
                _('Impossible de supprimer cette catégorie car elle est utilisée par des produits.')
            )
    return redirect('stock:liste_categories')


# Vues pour les produits
class ProduitListView(LoginRequiredMixin, ListView):
    model = Produit
    template_name = 'stock/produit_liste.html'
    context_object_name = 'produits'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrage par catégorie si spécifié
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Produit.objects.select_related('categorie', 'fournisseur')
        
        # Filtrage par recherche
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(designation__icontains=search_query) |
                Q(code__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filtrage par catégorie
        categorie_id = self.request.GET.get('categorie')
        if categorie_id:
            queryset = queryset.filter(categorie_id=categorie_id)
            
        # Filtrage par état du stock
        stock_filter = self.request.GET.get('stock')
        if stock_filter == 'alerte':
            queryset = queryset.filter(quantite_stock__lte=F('seuil_alerte'))
        elif stock_filter == 'faible':
            queryset = queryset.filter(quantite_stock__gt=0, quantite_stock__lte=F('seuil_alerte') * 2)
        elif stock_filter == 'disponible':
            queryset = queryset.filter(quantite_stock__gt=0)
        elif stock_filter == 'epuise':
            queryset = queryset.filter(quantite_stock__lte=0)
            
        # Tri par défaut
        return queryset.order_by('designation')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques rapides
        context['total_produits'] = Produit.objects.count()
        context['produits_alerte'] = Produit.objects.filter(
            quantite_stock__lte=F('seuil_alerte'),
            quantite_stock__gt=0
        ).count()
        context['produits_rupture'] = Produit.objects.filter(quantite_stock__lte=0).count()
        
        return context


class ProduitCreateView(LoginRequiredMixin, CreateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'stock/produit_form.html'
    
    def get_success_url(self):
        messages.success(self.request, 'Le produit a été créé avec succès.')
        return reverse('detail_produit', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ajouter un nouveau produit'
        return context
    
    def form_valid(self, form):
        form.instance.creer_par = self.request.user
        return super().form_valid(form)


class ProduitUpdateView(LoginRequiredMixin, UpdateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'stock/produit_form.html'
    
    def get_success_url(self):
        messages.success(self.request, 'Les modifications ont été enregistrées avec succès.')
        return reverse('detail_produit', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Modifier {self.object.design}'
        return context
    
    def form_valid(self, form):
        form.instance.modifie_par = self.request.user
        return super().form_valid(form)


def supprimer_produit(request, pk):
    """
    Vue pour supprimer un produit.
    """
    produit = get_object_or_404(Produit, pk=pk)
    
    if request.method == 'POST':
        # Vérifier s'il y a des mouvements de stock liés
        if produit.entrees.exists() or produit.sorties.exists():
            messages.error(request, 'Impossible de supprimer ce produit car il a des mouvements de stock associés.')
        else:
            produit.delete()
            messages.success(request, 'Le produit a été supprimé avec succès.')
            return redirect('liste_produits')
    
    # Si la méthode n'est pas POST ou s'il y a eu une erreur
    return redirect('detail_produit', pk=produit.pk)


class ProduitDetailView(LoginRequiredMixin, DetailView):
    model = Produit
    template_name = 'stock/produit_detail.html'
    context_object_name = 'produit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        produit = self.get_object()
        
        # Récupérer les 10 derniers mouvements de stock pour ce produit
        entrees = EntreeStock.objects.filter(produit=produit).select_related('fournisseur')
        sorties = SortieStock.objects.filter(produit=produit)
        
        # Préparer une liste combinée des mouvements avec leur type
        mouvements = []
        
        for entree in entrees.order_by('-date')[:50]:
            mouvements.append({
                'date': entree.date,
                'type_mouvement': 'entree',
                'reference': entree.reference,
                'quantite': entree.quantite,
                'solde_apres': entree.quantite_apres,
                'objet': entree
            })
            
        for sortie in sorties.order_by('-date')[:50]:
            mouvements.append({
                'date': sortie.date,
                'type_mouvement': 'sortie',
                'reference': sortie.reference,
                'quantite': sortie.quantite,
                'solde_apres': sortie.quantite_apres,
                'objet': sortie
            })
        
        # Trier les mouvements par date (du plus récent au plus ancien)
        mouvements.sort(key=lambda x: x['date'], reverse=True)
        
        # Limiter aux 20 derniers mouvements pour la vue d'ensemble
        context['mouvements'] = mouvements[:20]
        
        # Ajouter des statistiques supplémentaires
        context['total_entrees'] = entrees.aggregate(Sum('quantite'))['quantite__sum'] or 0
        context['total_sorties'] = sorties.aggregate(Sum('quantite'))['quantite__sum'] or 0
        
        return context


@login_required
@permission_required('stock.delete_produit', raise_exception=True)
def supprimer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        produit.delete()
        messages.success(request, _('Produit supprimé avec succès.'))
        return redirect('stock:liste_produits')
    return redirect('stock:detail_produit', pk=pk)


# Vues pour les fournisseurs
class FournisseurListView(LoginRequiredMixin, ListView):
    model = Fournisseur
    template_name = 'stock/fournisseur_liste.html'
    context_object_name = 'fournisseurs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Fournisseur.objects.annotate(
            nb_produits=Count('produits', distinct=True),
            nb_entrees=Count('entrees', distinct=True)
        )
        
        # Filtrage par recherche
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(nom__icontains=search_query) |
                Q(contact__icontains=search_query) |
                Q(adresse__icontains=search_query) |
                Q(telephone__icontains=search_query) |
                Q(email__icontains=search_query)
            )
            
        # Filtrage par statut
        statut = self.request.GET.get('statut')
        if statut == 'actif':
            queryset = queryset.filter(actif=True)
        elif statut == 'inactif':
            queryset = queryset.filter(actif=False)
            
        # Tri par défaut
        return queryset.order_by('nom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_statut'] = self.request.GET.get('statut', '')
        return context


class FournisseurDetailView(LoginRequiredMixin, DetailView):
    model = Fournisseur
    template_name = 'stock/fournisseur_detail.html'
    context_object_name = 'fournisseur'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fournisseur = self.get_object()
        
        # Produits fournis
        produits = fournisseur.produits.all()
        context['produits'] = produits
        
        # Dernières entrées
        entrees = fournisseur.entrees.select_related('produit').order_by('-date')[:10]
        context['dernieres_entrees'] = entrees
        
        # Statistiques
        context['total_entrees'] = fournisseur.entrees.count()
        context['total_produits'] = produits.count()
        
        return context


class FournisseurCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'stock/fournisseur_form.html'
    permission_required = 'stock.add_fournisseur'
    
    def get_success_url(self):
        messages.success(self.request, _('Fournisseur créé avec succès.'))
        return reverse('stock:detail_fournisseur', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Ajouter un nouveau fournisseur')
        return context
    
    def form_valid(self, form):
        form.instance.creer_par = self.request.user
        return super().form_valid(form)


class FournisseurUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'stock/fournisseur_form.html'
    permission_required = 'stock.change_fournisseur'
    
    def get_success_url(self):
        messages.success(self.request, _('Fournisseur mis à jour avec succès.'))
        return reverse('stock:detail_fournisseur', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier le fournisseur')
        return context
    
    def form_valid(self, form):
        form.instance.modifie_par = self.request.user
        return super().form_valid(form)


@login_required
@permission_required('stock.delete_fournisseur', raise_exception=True)
def supprimer_fournisseur(request, pk):
    """
    Vue pour supprimer un fournisseur.
    Vérifie d'abord qu'aucun produit ou entrée de stock n'est lié au fournisseur.
    """
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    
    if request.method == 'POST':
        # Vérifier s'il y a des produits ou des entrées liées
        if fournisseur.produits.exists() or fournisseur.entrees.exists():
            messages.error(
                request, 
                _('Impossible de supprimer ce fournisseur car il est lié à des produits ou des entrées de stock.')
            )
        else:
            fournisseur.delete()
            messages.success(request, _('Le fournisseur a été supprimé avec succès.'))
            return redirect('stock:liste_fournisseurs')
    
    # Si la méthode n'est pas POST ou s'il y a eu une erreur
    return redirect('stock:detail_fournisseur', pk=fournisseur.pk)


# Vues pour les mouvements de stock
class EntreeStockCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = EntreeStock
    form_class = EntreeStockForm
    template_name = 'stock/mouvements/entree_form.html'
    permission_required = 'stock.add_entreestock'
    
    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, _("L'entrée en stock a été enregistrée avec succès."))
        return response
    
    def get_success_url(self):
        return reverse('stock:detail_entree', kwargs={'pk': self.object.pk})


class EntreeStockDetailView(LoginRequiredMixin, DetailView):
    model = EntreeStock
    template_name = 'stock/entree_detail.html'
    context_object_name = 'entree'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Détails de l'entrée en stock")
        return context


@login_required
@permission_required('stock.delete_entreestock', raise_exception=True)
def annuler_entree(request, pk):
    """
    Annule une entrée en stock et met à jour le stock du produit.
    """
    entree = get_object_or_404(EntreeStock, pk=pk)
    
    if request.method == 'POST':
        # Vérifier si l'entrée n'a pas déjà été annulée
        if entree.annulee:
            messages.error(request, _("Cette entrée a déjà été annulée."))
            return redirect('stock:detail_entree', pk=entree.pk)
        
        # Vérifier s'il y a assez de stock pour annuler cette entrée
        if entree.produit.quantite_stock < entree.quantite:
            messages.error(
                request,
                _("Stock insuffisant pour annuler cette entrée. Stock actuel: %(stock)s, Quantité à retirer: %(quantite)s") % {
                    'stock': entree.produit.quantite_stock,
                    'quantite': entree.quantite
                }
            )
            return redirect('stock:detail_entree', pk=entree.pk)
        
        # Mise à jour du stock
        produit = entree.produit
        produit.quantite_stock -= entree.quantite
        produit.save(update_fields=['quantite_stock'])
        
        # Marquer l'entrée comme annulée
        entree.annulee = True
        entree.utilisateur_annulation = request.user
        entree.date_annulation = timezone.now()
        entree.save(update_fields=['annulee', 'utilisateur_annulation', 'date_annulation'])
        
        messages.success(request, _("L'entrée en stock a été annulée avec succès."))
        return redirect('stock:detail_entree', pk=entree.pk)
    
    return redirect('stock:liste_entrees')


class SortieStockCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SortieStock
    form_class = SortieStockForm
    template_name = 'stock/sortie_form.html'
    permission_required = 'stock.add_sortiestock'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        produit = form.cleaned_data['produit']
        quantite = form.cleaned_data['quantite']
        
        # Vérifier le stock disponible
        if produit.quantite_stock < quantite:
            form.add_error('quantite', _("Stock insuffisant. Stock disponible: %(stock)s") % {
                'stock': produit.quantite_stock
            })
            return self.form_invalid(form)
        
        response = super().form_valid(form)
        
        # Mise à jour du stock du produit
        produit.quantite_stock -= quantite
        produit.save(update_fields=['quantite_stock'])
        
        # Mise à jour de la quantité après mouvement
        self.object.quantite_apres = produit.quantite_stock
        self.object.save(update_fields=['quantite_apres'])
        
        messages.success(self.request, _("La sortie de stock a été enregistrée avec succès."))
        return response
    
    def get_success_url(self):
        return reverse('stock:detail_sortie', kwargs={'pk': self.object.pk})


class SortieStockDetailView(LoginRequiredMixin, DetailView):
    model = SortieStock
    template_name = 'stock/sortie_detail.html'
    context_object_name = 'sortie'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Détails de la sortie de stock")
        return context


@login_required
@permission_required('stock.delete_sortiestock', raise_exception=True)
def annuler_sortie(request, pk):
    """
    Annule une sortie de stock et remet les produits en stock.
    """
    sortie = get_object_or_404(SortieStock, pk=pk)
    
    if request.method == 'POST':
        # Vérifier si la sortie n'a pas déjà été annulée
        if sortie.annulee:
            messages.error(request, _("Cette sortie a déjà été annulée."))
            return redirect('stock:detail_sortie', pk=sortie.pk)
        
        # Mise à jour du stock
        produit = sortie.produit
        produit.quantite_stock += sortie.quantite
        produit.save(update_fields=['quantite_stock'])
        
        # Marquer la sortie comme annulée
        sortie.annulee = True
        sortie.utilisateur_annulation = request.user
        sortie.date_annulation = timezone.now()
        sortie.save(update_fields=['annulee', 'utilisateur_annulation', 'date_annulation'])
        
        messages.success(request, _("La sortie de stock a été annulée avec succès."))
        return redirect('stock:detail_sortie', pk=sortie.pk)
    
    return redirect('stock:liste_sorties')


class ListeEntreesView(LoginRequiredMixin, ListView):
    model = EntreeStock
    template_name = 'stock/entree_liste.html'
    context_object_name = 'entrees'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = EntreeStock.objects.select_related('produit', 'fournisseur', 'utilisateur')
        
        # Filtrage par produit
        produit_id = self.request.GET.get('produit')
        if produit_id:
            queryset = queryset.filter(produit_id=produit_id)
        
        # Filtrage par fournisseur
        fournisseur_id = self.request.GET.get('fournisseur')
        if fournisseur_id:
            queryset = queryset.filter(fournisseur_id=fournisseur_id)
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        if date_debut:
            queryset = queryset.filter(date__gte=date_debut)
        if date_fin:
            # Ajouter 1 jour pour inclure la date de fin
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(date__lt=date_fin_obj)
        
        # Filtrage par statut
        statut = self.request.GET.get('statut')
        if statut == 'annulees':
            queryset = queryset.filter(annulee=True)
        elif statut == 'actives':
            queryset = queryset.filter(annulee=False)
        
        # Tri par défaut
        return queryset.order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Données pour les filtres
        context['produits'] = Produit.objects.all().order_by('designation')
        context['fournisseurs'] = Fournisseur.objects.filter(actif=True).order_by('nom')
        
        # Paramètres de filtrage actuels
        context['selected_produit'] = self.request.GET.get('produit', '')
        context['selected_fournisseur'] = self.request.GET.get('fournisseur', '')
        context['date_debut'] = self.request.GET.get('date_debut', '')
        context['date_fin'] = self.request.GET.get('date_fin', '')
        context['selected_statut'] = self.request.GET.get('statut', '')
        
        # Statistiques
        if context['page_obj']:
            context['total_entrees'] = sum(e.quantite for e in context['page_obj'].object_list if not e.annulee)
            context['total_montant'] = sum(e.montant_total() for e in context['page_obj'].object_list if not e.annulee and e.prix_unitaire)
        
        return context


class ListeSortiesView(LoginRequiredMixin, ListView):
    model = SortieStock
    template_name = 'stock/sortie_liste.html'
    context_object_name = 'sorties'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SortieStock.objects.select_related('produit', 'utilisateur')
        
        # Filtrage par produit
        produit_id = self.request.GET.get('produit')
        if produit_id:
            queryset = queryset.filter(produit_id=produit_id)
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        if date_debut:
            queryset = queryset.filter(date__gte=date_debut)
        if date_fin:
            # Ajouter 1 jour pour inclure la date de fin
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(date__lt=date_fin_obj)
        
        # Filtrage par statut
        statut = self.request.GET.get('statut')
        if statut == 'annulees':
            queryset = queryset.filter(annulee=True)
        elif statut == 'actives':
            queryset = queryset.filter(annulee=False)
        
        # Tri par défaut
        return queryset.order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Données pour les filtres
        context['produits'] = Produit.objects.all().order_by('designation')
        
        # Paramètres de filtrage actuels
        context['selected_produit'] = self.request.GET.get('produit', '')
        context['date_debut'] = self.request.GET.get('date_debut', '')
        context['date_fin'] = self.request.GET.get('date_fin', '')
        context['selected_statut'] = self.request.GET.get('statut', '')
        
        # Statistiques
        if context['page_obj']:
            context['total_sorties'] = sum(s.quantite for s in context['page_obj'].object_list if not s.annulee)
            if any(s.prix_unitaire for s in context['page_obj'].object_list if not s.annulee):
                context['total_montant'] = sum(s.montant_total() for s in context['page_obj'].object_list if not s.annulee and s.prix_unitaire)
        
        return context



class SortieStockCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SortieStock
    form_class = SortieStockForm
    template_name = 'stock/sortie_form.html'
    permission_required = 'stock.add_sortiestock'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        produit = form.cleaned_data['produit']
        quantite = form.cleaned_data['quantite']
        
        # Vérifier le stock disponible
        if produit.quantite_stock < quantite:
            form.add_error('quantite', _("Stock insuffisant. Stock disponible: %(stock)s") % {
                'stock': produit.quantite_stock
            })
            return self.form_invalid(form)
        
        response = super().form_valid(form)
        
        # Mise à jour du stock du produit
        produit.quantite_stock -= quantite
        produit.save(update_fields=['quantite_stock'])
        
        # Mise à jour de la quantité après mouvement
        self.object.quantite_apres = produit.quantite_stock
        self.object.save(update_fields=['quantite_apres'])
        
        messages.success(self.request, _("La sortie de stock a été enregistrée avec succès."))
        return response
    
    def get_success_url(self):
        return reverse('stock:detail_sortie', kwargs={'pk': self.object.pk})


class SortieStockDetailView(LoginRequiredMixin, DetailView):
    model = SortieStock
    template_name = 'stock/sortie_detail.html'
    context_object_name = 'sortie'


# Vues pour les listes d'entrées et sorties
class ListeEntreesView(LoginRequiredMixin, ListView):
    model = EntreeStock
    template_name = 'stock/mouvements/entree_liste.html'
    context_object_name = 'entrees'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = EntreeStock.objects.select_related('produit', 'fournisseur')
        
        # Filtrage par recherche
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(produit__designation__icontains=search_query) |
                Q(produit__code__icontains=search_query) |
                Q(reference__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if date_debut:
            queryset = queryset.filter(date__date__gte=date_debut)
        if date_fin:
            # Ajouter un jour pour inclure la date de fin
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(date__date__lt=date_fin_obj)
        
        # Tri par défaut
        return queryset.order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_entrees'] = self.get_queryset().count()
        context['total_quantite'] = self.get_queryset().aggregate(
            total=Sum('quantite')
        )['total'] or 0
        
        # Valeurs pour les filtres
        context['search_query'] = self.request.GET.get('q', '')
        context['date_debut'] = self.request.GET.get('date_debut', '')
        context['date_fin'] = self.request.GET.get('date_fin', '')
        
        # Dernières entrées pour le panneau latéral
        context['dernieres_entrees'] = EntreeStock.objects.select_related('produit')\
            .order_by('-date')[:5]
        
        return context


class ListeSortiesView(LoginRequiredMixin, ListView):
    model = SortieStock
    template_name = 'stock/mouvements/sortie_liste.html'
    context_object_name = 'sorties'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = SortieStock.objects.select_related('produit')
        
        # Filtrage par recherche
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(produit__designation__icontains=search_query) |
                Q(produit__code__icontains=search_query) |
                Q(client__icontains=search_query) |
                Q(reference__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if date_debut:
            queryset = queryset.filter(date__date__gte=date_debut)
        if date_fin:
            # Ajouter un jour pour inclure la date de fin
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(date__date__lt=date_fin_obj)
        
        # Tri par défaut
        return queryset.order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_sorties'] = self.get_queryset().count()
        context['total_quantite'] = self.get_queryset().aggregate(
            total=Sum('quantite')
        )['total'] or 0
        
        # Calcul du chiffre d'affaires
        context['chiffre_affaires'] = self.get_queryset().aggregate(
            total=Sum(F('quantite') * F('prix_unitaire'), output_field=DecimalField())
        )['total'] or 0
        
        # Valeurs pour les filtres
        context['search_query'] = self.request.GET.get('q', '')
        context['date_debut'] = self.request.GET.get('date_debut', '')
        context['date_fin'] = self.request.GET.get('date_fin', '')
        
        # Dernières sorties pour le panneau latéral
        context['dernieres_sorties'] = SortieStock.objects.select_related('produit')\
            .order_by('-date')[:5]
        
        return context


# Vues pour les rapports
@login_required
def rapport_stock_faible(request):
    """
    Rapport des produits en dessous du seuil d'alerte.
    Affiche les produits dont la quantité en stock est inférieure ou égale au seuil d'alerte.
    """
    produits = Produit.objects.filter(
        quantite_stock__lte=F('seuil_alerte'),
        actif=True
    ).select_related('categorie', 'fournisseur')\
        .order_by('quantite_stock')
    
    context = {
        'produits': produits,
        'titre': _('Rapport des produits en alerte de stock'),
        'total_produits_alerte': produits.count(),
    }
    return render(request, 'stock/rapports/stock_faible.html', context)


@login_required
def rapport_mouvements(request):
    """
    Rapport des mouvements de stock sur une période donnée.
    Permet de filtrer les entrées et sorties de stock par plage de dates.
    """
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    # Validation des dates
    try:
        if date_debut:
            date_debut = timezone.datetime.strptime(date_debut, '%Y-%m-%d').date()
        if date_fin:
            date_fin = timezone.datetime.strptime(date_fin, '%Y-%m-%d').date()
            
        # Vérifier que la date de début est avant la date de fin
        if date_debut and date_fin and date_debut > date_fin:
            messages.error(request, _("La date de début doit être antérieure à la date de fin."))
            date_debut, date_fin = None, None
    except ValueError:
        messages.error(request, _("Format de date invalide. Utilisez le format AAAA-MM-JJ."))
        date_debut, date_fin = None, None
    
    # Construction des requêtes avec filtrage
    entrees = EntreeStock.objects.all()
    sorties = SortieStock.objects.all()
    
    if date_debut:
        entrees = entrees.filter(date__gte=date_debut)
        sorties = sorties.filter(date__gte=date_debut)
    
    if date_fin:
        # Ajouter 1 jour pour inclure la date de fin
        date_fin_plus_1 = date_fin + timezone.timedelta(days=1)
        entrees = entrees.filter(date__lt=date_fin_plus_1)
        sorties = sorties.filter(date__lt=date_fin_plus_1)
    
    # Optimisation des requêtes avec select_related
    entrees = entrees.select_related('produit', 'fournisseur', 'utilisateur')
    sorties = sorties.select_related('produit', 'utilisateur')
    
    # Calcul des totaux
    total_entrees = entrees.aggregate(total=Sum('quantite'))['total'] or 0
    total_sorties = sorties.aggregate(total=Sum('quantite'))['total'] or 0
    
    context = {
        'date_debut': date_debut.strftime('%Y-%m-%d') if date_debut else '',
        'date_fin': date_fin.strftime('%Y-%m-%d') if date_fin else '',
        'entrees': entrees.order_by('-date'),
        'sorties': sorties.order_by('-date'),
        'total_entrees': total_entrees,
        'total_sorties': total_sorties,
        'titre': _('Rapport des mouvements de stock'),
    }
    return render(request, 'stock/rapports/mouvements.html', context)


# Vues pour l'API (utilisées pour les requêtes AJAX)
@login_required
def api_produits_par_categorie(request):
    """
    API pour obtenir le nombre de produits par catégorie.
    Utilisé pour les graphiques du tableau de bord.
    Retourne du JSON avec le nom de la catégorie, le nombre de produits et le stock total.
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Requête non autorisée'}, status=403)
    
    try:
        # Récupération des données avec agrégation
        donnees = Categorie.objects.filter(actif=True).annotate(
            nb_produits=Count('produit', filter=Q(produit__actif=True)),
            stock_total=Coalesce(Sum('produit__quantite_stock', filter=Q(produit__actif=True)), 0)
        ).values('id', 'nom', 'nb_produits', 'stock_total').order_by('nom')
        
        return JsonResponse({
            'status': 'success',
            'data': list(donnees)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def api_mouvements_mensuels(request):
    """
    API pour obtenir les mouvements de stock mensuels.
    Utilisé pour les graphiques d'évolution du stock.
    Retourne les quantités mensuelles d'entrées et sorties.
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Requête non autorisée'}, status=403)
    
    try:
        from django.db.models.functions import TruncMonth
        
        # Période par défaut : 12 derniers mois
        date_debut = timezone.now() - timezone.timedelta(days=365)
        
        # Récupération des entrées mensuelles
        entrees = EntreeStock.objects.filter(
            date__gte=date_debut
        ).annotate(
            mois=TruncMonth('date')
        ).values('mois').annotate(
            total=Sum('quantite')
        ).order_by('mois')
        
        # Récupération des sorties mensuelles
        sorties = SortieStock.objects.filter(
            date__gte=date_debut
        ).annotate(
            mois=TruncMonth('date')
        ).values('mois').annotate(
            total=Sum('quantite')
        ).order_by('mois')
        
        # Formatage des dates pour le frontend
        def format_mois(mois_data):
            return [{
                'mois': item['mois'].strftime('%Y-%m'),
                'total': float(item['total'])  # Conversion en float pour JSON
            } for item in mois_data if item['total']]
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'entrees': format_mois(entrees),
                'sorties': format_mois(sorties)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
f r o m   d j a n g o . v i e w s . g e n e r i c   i m p o r t   D e t a i l V i e w  
 f r o m   d j a n g o . c o n t r i b . a u t h . m i x i n s   i m p o r t   L o g i n R e q u i r e d M i x i n  
 f r o m   d j a n g o . u t i l s . t r a n s l a t i o n   i m p o r t   g e t t e x t _ l a z y   a s   _  
  
 f r o m   . m o d e l s   i m p o r t   S o r t i e S t o c k  
  
 c l a s s   S o r t i e S t o c k D e t a i l V i e w ( L o g i n R e q u i r e d M i x i n ,   D e t a i l V i e w ) :  
         " " "  
         V u e   p o u r   a f f i c h e r   l e s   d � � t a i l s   d ' u n e   s o r t i e   d e   s t o c k .  
         " " "  
         m o d e l   =   S o r t i e S t o c k  
         t e m p l a t e _ n a m e   =   ' s t o c k / m o u v e m e n t s / s o r t i e _ d e t a i l . h t m l '  
         c o n t e x t _ o b j e c t _ n a m e   =   ' s o r t i e '  
          
         d e f   g e t _ c o n t e x t _ d a t a ( s e l f ,   * * k w a r g s ) :  
                 c o n t e x t   =   s u p e r ( ) . g e t _ c o n t e x t _ d a t a ( * * k w a r g s )  
                 c o n t e x t [ ' t i t l e ' ]   =   _ ( " D � � t a i l s   d e   l a   s o r t i e   d e   s t o c k " )  
                 r e t u r n   c o n t e x t  
 