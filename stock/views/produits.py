from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from ..models import Produit, Fournisseur
from ..forms import ProduitForm

class ProduitListView(LoginRequiredMixin, ListView):
    model = Produit
    template_name = 'stock/produits/liste.html'
    context_object_name = 'produits'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Produit.objects.select_related('categorie', 'fournisseur').order_by('designation')
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(designation__icontains=search_query) |
                Q(code__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Produit.CATEGORIE_CHOICES
        context['fournisseurs'] = Fournisseur.objects.all()
        context['title'] = _("Liste des produits")
        return context

class ProduitDetailView(LoginRequiredMixin, DetailView):
    model = Produit
    template_name = 'stock/produits/detail.html'
    context_object_name = 'produit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Détails du produit")
        return context

class ProduitCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'stock/produits/form.html'
    permission_required = 'stock.add_produit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Ajouter un produit")
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("Le produit a été ajouté avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('stock:detail_produit', kwargs={'pk': self.object.pk})

class ProduitUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'stock/produits/form.html'
    permission_required = 'stock.change_produit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier le produit")
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("Le produit a été mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('stock:detail_produit', kwargs={'pk': self.object.pk})

def supprimer_produit(request, pk):
    if not request.user.has_perm('stock.delete_produit'):
        messages.error(request, _("Vous n'avez pas la permission de supprimer ce produit."))
        return redirect('stock:produit-list')
    
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        produit.delete()
        messages.success(request, _("Le produit a été supprimé avec succès."))
        return redirect('stock:produit-list')
    
    return redirect('stock:detail_produit', pk=pk)
