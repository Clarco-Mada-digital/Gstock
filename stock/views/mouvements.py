from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q, F, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse

from ..models import EntreeStock, SortieStock, Produit, Notification
from ..forms import EntreeStockForm, SortieStockForm

# Vues pour les entrées de stock
class ListeEntreesView(LoginRequiredMixin, ListView):
    model = EntreeStock
    template_name = 'stock/mouvements/entree_liste.html'
    context_object_name = 'entrees'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = EntreeStock.objects.select_related('produit', 'utilisateur').order_by('-date')
        
        search_query = self.request.GET.get('q')
        produit_id = self.request.GET.get('produit')
        
        if search_query:
            queryset = queryset.filter(
                Q(produit__designation__icontains=search_query) |
                Q(reference__icontains=search_query) |
                Q(notes__icontains=search_query) |
                Q(fournisseur__nom__icontains=search_query)
            )
            
        if produit_id:
            queryset = queryset.filter(produit_id=produit_id)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Historique des entrées de stock")
        
        # Ajout des produits pour le filtre
        from ..models import Produit
        context['produits'] = Produit.objects.all().order_by('designation')
        
        # Ajout des paramètres de recherche pour la pagination
        context['search_query'] = self.request.GET.get('q', '')
        context['produit_filter'] = self.request.GET.get('produit', '')
        
        return context

class EntreeStockCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = EntreeStock
    form_class = EntreeStockForm
    template_name = 'stock/mouvements/entree_form.html'
    permission_required = 'stock.add_entreestock'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Nouvelle entrée de stock")
        return context
    
    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        
        # Mise à jour du stock du produit
        produit = form.cleaned_data['produit']
        quantite = form.cleaned_data['quantite']
        produit.quantite_stock = F('quantite_stock') + quantite
        produit.save(update_fields=['quantite_stock'])
        
        messages.success(self.request, _("L'entrée de stock a été enregistrée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('stock:detail_entree', kwargs={'pk': self.object.pk})

class EntreeStockDetailView(LoginRequiredMixin, DetailView):
    model = EntreeStock
    template_name = 'stock/mouvements/entree_detail.html'
    context_object_name = 'entree'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Détails de l'entrée de stock")
        return context


class EntreeStockUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = EntreeStock
    form_class = EntreeStockForm
    template_name = 'stock/mouvements/entree_form.html'
    permission_required = 'stock.change_entreestock'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier l'entrée de stock")
        return context
    
    def form_valid(self, form):
        # Récupérer l'ancienne quantité pour ajuster le stock
        old_entree = EntreeStock.objects.get(pk=self.object.pk)
        difference = form.cleaned_data['quantite'] - old_entree.quantite
        
        # Mettre à jour le stock du produit
        produit = form.cleaned_data['produit']
        produit.quantite_stock = F('quantite_stock') + difference
        produit.save(update_fields=['quantite_stock'])
        
        messages.success(self.request, _("L'entrée de stock a été mise à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('stock:detail_entree', kwargs={'pk': self.object.pk})

# Vues pour les sorties de stock
class ListeSortiesView(LoginRequiredMixin, ListView):
    model = SortieStock
    template_name = 'stock/mouvements/sortie_liste.html'
    context_object_name = 'sorties'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SortieStock.objects.select_related('produit', 'utilisateur').order_by('-date')
        
        search_query = self.request.GET.get('q')
        produit_id = self.request.GET.get('produit')
        
        if search_query:
            queryset = queryset.filter(
                Q(produit__designation__icontains=search_query) |
                Q(reference__icontains=search_query) |
                Q(notes__icontains=search_query) |
                Q(client__icontains=search_query)
            )
            
        if produit_id:
            queryset = queryset.filter(produit_id=produit_id)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Historique des sorties de stock")
        
        # Ajout des produits pour le filtre
        from ..models import Produit
        context['produits'] = Produit.objects.all().order_by('designation')
        
        # Ajout des paramètres de recherche pour la pagination
        context['search_query'] = self.request.GET.get('q', '')
        context['produit_filter'] = self.request.GET.get('produit', '')
        
        return context

class SortieStockCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SortieStock
    form_class = SortieStockForm
    template_name = 'stock/mouvements/sortie_form.html'
    permission_required = 'stock.add_sortiestock'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Nouvelle sortie de stock")
        return context
    
    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        produit = form.cleaned_data['produit']
        quantite = form.cleaned_data['quantite']
        
        # Vérifier si le stock est suffisant
        if produit.quantite_stock < quantite:
            form.add_error('quantite', _("La quantité en stock est insuffisante."))
            return self.form_invalid(form)
        
        # Mise à jour du stock du produit
        produit.quantite_stock = F('quantite_stock') - quantite
        produit.save(update_fields=['quantite_stock'])
        
        messages.success(self.request, _("La sortie de stock a été enregistrée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('stock:detail_sortie', kwargs={'pk': self.object.pk})

class SortieStockDetailView(LoginRequiredMixin, DetailView):
    model = SortieStock
    template_name = 'stock/mouvements/sortie_detail.html'
    context_object_name = 'sortie'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Détails de la sortie de stock")
        return context

def annuler_entree(request, pk):
    """
    Annule une entrée de stock et met à jour les quantités en conséquence.
    """
    if not request.user.has_perm('stock.delete_entreestock'):
        messages.error(request, _("Vous n'avez pas la permission d'annuler cette entrée."))
        return redirect('stock:liste_entrees')
    
    entree = get_object_or_404(EntreeStock, pk=pk)
    
    if request.method == 'POST':
        # Vérifier si le stock actuel est suffisant pour annuler l'entrée
        if entree.produit.quantite_stock < entree.quantite:
            messages.error(
                request,
                _("Impossible d'annuler cette entrée car le stock actuel est insuffisant.")
            )
            return redirect('stock:detail_entree', pk=pk)
        
        # Mettre à jour le stock
        entree.produit.quantite_stock = F('quantite_stock') - entree.quantite
        entree.produit.save(update_fields=['quantite_stock'])
        
        # Marquer l'entrée comme annulée
        entree.annulee = True
        entree.save(update_fields=['annulee'])
        
        messages.success(request, _("L'entrée de stock a été annulée avec succès."))
        return redirect('stock:liste_entrees')
    
    return redirect('stock:detail_entree', pk=pk)

def annuler_sortie(request, pk):
    """
    Annule une sortie de stock et met à jour les quantités en conséquence.
    """
    if not request.user.has_perm('stock.delete_sortiestock'):
        messages.error(request, _("Vous n'avez pas la permission d'annuler cette sortie."))
        return redirect('stock:liste_sorties')
    
    sortie = get_object_or_404(SortieStock, pk=pk)
    
    if request.method == 'POST':
        # Mettre à jour le stock
        sortie.produit.quantite_stock = F('quantite_stock') + sortie.quantite
        sortie.produit.save(update_fields=['quantite_stock'])
        
        # Marquer la sortie comme annulée
        sortie.annulee = True
        sortie.save(update_fields=['annulee'])
        
        messages.success(request, _("La sortie de stock a été annulée avec succès."))
        return redirect('stock:liste_sorties')
    
    return redirect('stock:detail_sortie', pk=pk)
