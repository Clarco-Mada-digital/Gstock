from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _


from ..models import Categorie, Produit
from ..forms import CategorieForm

class CategorieListView(LoginRequiredMixin, ListView):
    model = Categorie
    template_name = 'stock/categories/liste.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        queryset = Categorie.objects.annotate(
            nb_produits=Count('produit', distinct=True)
        ).order_by('nom')
        
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(nom__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Liste des catégories")
        return context

class CategorieCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Categorie
    form_class = CategorieForm
    template_name = 'stock/categories/form.html'
    permission_required = 'stock.add_categorie'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Ajouter une catégorie")
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("La catégorie a été ajoutée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('stock:liste_categories')

class CategorieUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Categorie
    form_class = CategorieForm
    template_name = 'stock/categories/form.html'
    permission_required = 'stock.change_categorie'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier la catégorie")
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("La catégorie a été mise à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('stock:liste_categories')

def supprimer_categorie(request, pk):
    if not request.user.has_perm('stock.delete_categorie'):
        messages.error(request, _("Vous n'avez pas la permission de supprimer cette catégorie."))
        return redirect('stock:liste_categories')
    
    categorie = get_object_or_404(Categorie, pk=pk)
    
    # Vérifier si la catégorie est utilisée par des produits
    if categorie.produit_set.exists():
        messages.error(
            request,
            _("Impossible de supprimer cette catégorie car elle est utilisée par des produits.")
        )
        return redirect('stock:liste_categories')
    
    if request.method == 'POST':
        categorie.delete()
        messages.success(request, _("La catégorie a été supprimée avec succès."))
    
    return redirect('stock:liste_categories')
