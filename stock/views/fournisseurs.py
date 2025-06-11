from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _


from ..models import Fournisseur, Produit
from ..forms import FournisseurForm

class FournisseurListView(LoginRequiredMixin, ListView):
    model = Fournisseur
    template_name = 'stock/fournisseurs/liste.html'
    context_object_name = 'fournisseurs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Fournisseur.objects.annotate(
            nb_produits=Count('produit', distinct=True)
        ).order_by('nom')
        
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(nom__icontains=search_query) |
                Q(contact__icontains=search_query) |
                Q(adresse__icontains=search_query)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Liste des fournisseurs")
        return context

class FournisseurDetailView(LoginRequiredMixin, DetailView):
    model = Fournisseur
    template_name = 'stock/fournisseurs/detail.html'
    context_object_name = 'fournisseur'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Détails du fournisseur")
        context['produits'] = self.object.produit_set.all()
        return context

class FournisseurCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'stock/fournisseurs/form.html'
    permission_required = 'stock.add_fournisseur'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Ajouter un fournisseur")
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("Le fournisseur a été ajouté avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('stock:detail_fournisseur', kwargs={'pk': self.object.pk})

class FournisseurUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'stock/fournisseurs/form.html'
    permission_required = 'stock.change_fournisseur'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier le fournisseur")
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("Le fournisseur a été mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('stock:detail_fournisseur', kwargs={'pk': self.object.pk})

def supprimer_fournisseur(request, pk):
    if not request.user.has_perm('stock.delete_fournisseur'):
        messages.error(request, _("Vous n'avez pas la permission de supprimer ce fournisseur."))
        return redirect('stock:liste_fournisseurs')
    
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    
    # Vérifier si le fournisseur est utilisé par des produits
    if fournisseur.produit_set.exists():
        messages.error(
            request,
            _("Impossible de supprimer ce fournisseur car il est associé à des produits.")
        )
        return redirect('stock:detail_fournisseur', pk=pk)
    
    if request.method == 'POST':
        fournisseur.delete()
        messages.success(request, _("Le fournisseur a été supprimé avec succès."))
    
    return redirect('stock:liste_fournisseurs')
