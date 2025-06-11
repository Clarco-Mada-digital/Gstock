from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F, Sum, Case, When, Value, IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta

from ..models import EntreeStock, SortieStock, Produit

class HistoriqueMouvementsView(LoginRequiredMixin, TemplateView):
    template_name = 'stock/historique/mouvements.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupération des paramètres de filtre
        periode = self.request.GET.get('periode', '7')
        produit_id = self.request.GET.get('produit')
        type_mouvement = self.request.GET.get('type')
        
        # Calcul des dates en fonction de la période sélectionnée
        date_fin = timezone.now()
        if periode == '7':
            date_debut = date_fin - timedelta(days=7)
            periode_libelle = "7 derniers jours"
        elif periode == '30':
            date_debut = date_fin - timedelta(days=30)
            periode_libelle = "30 derniers jours"
        elif periode == '90':
            date_debut = date_fin - timedelta(days=90)
            periode_libelle = "3 derniers mois"
        else:
            date_debut = date_fin - timedelta(days=7)
            periode_libelle = "7 derniers jours"
        
        # Filtrage des mouvements
        entrees = EntreeStock.objects.filter(date__range=[date_debut, date_fin])
        sorties = SortieStock.objects.filter(date__range=[date_debut, date_fin])
        
        # Filtrage par produit si spécifié
        if produit_id:
            produit = Produit.objects.get(pk=produit_id)
            entrees = entrees.filter(produit=produit)
            sorties = sorties.filter(produit=produit)
            context['produit_selectionne'] = produit
        
        # Filtrage par type de mouvement
        if type_mouvement == 'entree':
            sorties = sorties.none()
            context['type_selectionne'] = 'entree'
        elif type_mouvement == 'sortie':
            entrees = entrees.none()
            context['type_selectionne'] = 'sortie'
        
        # Agrégation des données pour les graphiques
        mouvements_par_jour = []
        mouvements_par_produit = {}
        
        # Récupération des 10 produits les plus actifs
        produits_actifs = list(entrees.values('produit__designation').annotate(
            total=Sum('quantite')
        ).order_by('-total')[:10])
        
        # Préparation des données pour le graphique d'évolution
        for i in range((date_fin - date_debut).days + 1):
            date = date_debut + timedelta(days=i)
            entree_jour = entrees.filter(date__date=date).aggregate(total=Sum('quantite'))['total'] or 0
            sortie_jour = sorties.filter(date__date=date).aggregate(total=Sum('quantite'))['total'] or 0
            
            mouvements_par_jour.append({
                'date': date,
                'entrees': entree_jour,
                'sorties': sortie_jour
            })
        
        # Préparation des données pour le graphique par produit
        for produit in produits_actifs:
            produit_designation = produit['produit__designation']
            entrees_produit = entrees.filter(produit__designation=produit_designation).aggregate(total=Sum('quantite'))['total'] or 0
            sorties_produit = sorties.filter(produit__designation=produit_designation).aggregate(total=Sum('quantite'))['total'] or 0
            
            mouvements_par_produit[produit_designation] = {
                'entrees': entrees_produit,
                'sorties': sorties_produit,
                'solde': entrees_produit - sorties_produit
            }
        
        # Préparation des données pour le tableau des mouvements récents
        mouvements_recents = []
        for entree in entrees.order_by('-date')[:50]:
            mouvements_recents.append({
                'date': entree.date,
                'type': 'entree',
                'produit': entree.produit,
                'quantite': entree.quantite,
                'prix_unitaire': entree.prix_unitaire,
                'total': entree.quantite * entree.prix_unitaire,
                'utilisateur': entree.utilisateur,
                'reference': entree.reference
            })
            
        for sortie in sorties.order_by('-date')[:50]:
            mouvements_recents.append({
                'date': sortie.date,
                'type': 'sortie',
                'produit': sortie.produit,
                'quantite': sortie.quantite,
                'prix_unitaire': sortie.prix_unitaire,
                'total': sortie.quantite * sortie.prix_unitaire,
                'utilisateur': sortie.utilisateur,
                'reference': sortie.reference
            })
        
        # Tri des mouvements par date décroissante
        mouvements_recents = sorted(mouvements_recents, key=lambda x: x['date'], reverse=True)[:50]
        
        # Calcul des totaux
        total_entrees = sum(e['entrees'] for e in mouvements_par_jour)
        total_sorties = sum(e['sorties'] for e in mouvements_par_jour)
        
        # Préparation du contexte
        context.update({
            'periode_libelle': periode_libelle,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'mouvements_par_jour': mouvements_par_jour,
            'mouvements_par_produit': mouvements_par_produit,
            'mouvements_recents': mouvements_recents,
            'total_entrees': total_entrees,
            'total_sorties': total_sorties,
            'produits': Produit.objects.order_by('designation'),
            'active_tab': 'historique',
        })
        
        return context
