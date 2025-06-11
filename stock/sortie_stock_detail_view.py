from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _

from .models import SortieStock

class SortieStockDetailView(LoginRequiredMixin, DetailView):
    """
    Vue pour afficher les détails d'une sortie de stock.
    """
    model = SortieStock
    template_name = 'stock/mouvements/sortie_detail.html'
    context_object_name = 'sortie'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Détails de la sortie de stock")
        return context
