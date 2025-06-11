from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Q, Count
from django.utils import timezone
from django.db import connection
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from ..models import Produit, EntreeStock, SortieStock, Notification, Categorie, Fournisseur

@login_required
def accueil(request):
    # Récupération des statistiques principales avec une seule requête
    stats_produits = Produit.objects.aggregate(
        total=Count('id'),
        en_alerte=Count('id', filter=Q(quantite_stock__lte=F('seuil_alerte'))),
        valeur_totale=Sum(F('quantite_stock') * F('prix_vente'))
    )
    
    # Calcul des mouvements des 7 derniers jours
    date_limite = timezone.now() - timedelta(days=7)
    stats_mouvements = {
        'entrees': EntreeStock.objects.filter(date__gte=date_limite).count(),
        'sorties': SortieStock.objects.filter(date__gte=date_limite).count(),
    }
    
    # Derniers mouvements avec une seule requête
    dernieres_entrees = EntreeStock.objects.select_related('produit', 'utilisateur')\
        .order_by('-date')[:5]
    dernieres_sorties = SortieStock.objects.select_related('produit', 'utilisateur')\
        .order_by('-date')[:5]
    
    # Combiner et trier les entrées et sorties
    derniers_mouvements = sorted(
        list(dernieres_entrees) + list(dernieres_sorties),
        key=lambda x: x.date,
        reverse=True
    )[:5]
    
    # Produits en alerte avec leur catégorie
    produits_en_alerte = Produit.objects.select_related('categorie')\
        .filter(quantite_stock__lte=F('seuil_alerte'))\
        .order_by('quantite_stock')[:5]
    
    # Statistiques par catégorie
    categories_stats = Categorie.objects.annotate(
        nb_produits=Count('produit'),
        nb_alertes=Count('produit', filter=Q(produit__quantite_stock__lte=F('produit__seuil_alerte')))
    ).order_by('-nb_produits')[:5]
    
    # Préparer les données pour le graphique
    today = timezone.now().date()
    dates = [(today - timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
    
    # Récupérer les données pour le graphique
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
            date(date) as jour, 
            SUM(CASE WHEN type_mouvement = 'entree' THEN quantite ELSE 0 END) as entrees,
            SUM(CASE WHEN type_mouvement = 'sortie' THEN quantite ELSE 0 END) as sorties
        FROM (
            SELECT date, quantite, 'entree' as type_mouvement FROM stock_entreestock
            WHERE date >= %s
            UNION ALL
            SELECT date, quantite, 'sortie' as type_mouvement FROM stock_sortiestock
            WHERE date >= %s
        ) as mouvements
        GROUP BY date(date)
        ORDER BY jour DESC
        LIMIT 7
    """, [date_limite, date_limite])
    
    # Traiter les résultats
    mouvements_par_jour = {}
    for date, entrees, sorties in cursor.fetchall():
        # Convertir la date en objet date si ce n'est pas déjà le cas
        if isinstance(date, str):
            from datetime import datetime
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            date_str = date_obj.strftime('%d/%m')
        else:
            date_str = date.strftime('%d/%m')
        mouvements_par_jour[date_str] = {'entrees': int(entrees or 0), 'sorties': int(sorties or 0)}
    
    # Préparer les séries pour le graphique
    serie_entrees = []
    serie_sorties = []
    
    for date in dates:
        data = mouvements_par_jour.get(date, {'entrees': 0, 'sorties': 0})
        serie_entrees.append(data['entrees'])
        serie_sorties.append(data['sorties'])
    
    # Récupérer les notifications non vues
    notifications_non_lues = Notification.objects.filter(
        utilisateur=request.user,
        vue=False
    ).order_by('-date_creation')[:10]
    
    # Préparer le contexte
    context = {
        'title': _('Tableau de bord'),
        'dates': dates,
        'serie_entrees': serie_entrees,
        'serie_sorties': serie_sorties,
        'stats': {
            'total_produits': stats_produits['total'],
            'produits_en_alerte': stats_produits['en_alerte'],
            'valeur_totale': stats_produits['valeur_totale'] or 0,
            'mouvements_7j': stats_mouvements['entrees'] + stats_mouvements['sorties'],
            'total_mouvements': len(derniers_mouvements),
            'entrees_7j': stats_mouvements['entrees'],
            'sorties_7j': stats_mouvements['sorties'],
            'nb_categories': Categorie.objects.count(),
            'nb_fournisseurs': Fournisseur.objects.count(),
        },
        'produits_alerte_liste': produits_en_alerte,
        'categories_stats': categories_stats,
        'derniers_mouvements': derniers_mouvements[:10],
        'dernieres_entrees': dernieres_entrees,
        'dernieres_sorties': dernieres_sorties,
        'notifications': notifications_non_lues,
    }
    return render(request, 'stock/accueil.html', context)
