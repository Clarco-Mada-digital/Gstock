from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q, F, Sum, Count, Case, When, Value, IntegerField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from datetime import timedelta
import io
import xlsxwriter
from xhtml2pdf import pisa

from ..models import Produit, EntreeStock, SortieStock, Categorie
from ..forms import RapportMouvementsForm

def rapport_stock_faible(request):
    """
    Affiche la liste des produits dont le stock est en dessous du seuil d'alerte.
    """
    if not request.user.has_perm('stock.view_rapport_stock_faible'):
        messages.error(request, _("Vous n'avez pas la permission d'accéder à ce rapport."))
        return redirect('stock:accueil')
    
    # Récupérer les produits dont le stock est inférieur ou égal au seuil d'alerte
    produits = Produit.objects.filter(
        quantite_stock__lte=F('seuil_alerte')
    ).select_related('categorie', 'fournisseur').order_by('quantite_stock')
    
    # Calculer la valeur totale du stock en alerte
    valeur_totale = sum(p.quantite_stock * p.prix_vente for p in produits)
    
    # Préparer les données pour le graphique
    categories = {}
    for produit in produits:
        categorie = produit.categorie.nom if produit.categorie else _("Sans catégorie")
        if categorie not in categories:
            categories[categorie] = {
                'quantite': 0,
                'valeur': 0,
                'produits': []
            }
        categories[categorie]['quantite'] += produit.quantite_stock
        categories[categorie]['valeur'] += produit.quantite_stock * produit.prix_vente
        categories[categorie]['produits'].append(produit)
    
    # Trier les catégories par quantité (décroissant)
    categories_triees = sorted(
        categories.items(),
        key=lambda x: x[1]['quantite'],
        reverse=True
    )
    
    context = {
        'title': _("Rapport de stock faible"),
        'produits': produits,
        'categories': dict(categories_triees),
        'total_produits': len(produits),
        'valeur_totale': valeur_totale,
    }
    
    # Gérer les exports
    export_format = request.GET.get('export')
    if export_format == 'pdf':
        return generer_pdf_rapport_stock_faible(produits, context)
    elif export_format == 'excel':
        return generer_excel_rapport_stock_faible(produits, context)
    
    return render(request, 'stock/rapports/stock_faible.html', context)

def generer_pdf_rapport_stock_faible(queryset, context):
    """Génère un PDF du rapport de stock faible."""
    template = get_template('stock/rapports/export/stock_faible_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_stock_faible.pdf"'
    
    # Créer le PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)
    
    return response

def generer_excel_rapport_stock_faible(queryset, context):
    """Génère un fichier Excel du rapport de stock faible."""
    output = io.BytesIO()
    
    # Créer un nouveau classeur Excel
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    
    # Formats
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })
    
    # Écrire les en-têtes
    headers = [
        _("Référence"),
        _("Désignation"),
        _("Catégorie"),
        _("Stock actuel"),
        _("Seuil d'alerte"),
        _("Prix unitaire"),
        _("Valeur totale")
    ]
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Écrire les données
    for row, produit in enumerate(queryset, start=1):
        worksheet.write(row, 0, produit.code)
        worksheet.write(row, 1, produit.designation)
        worksheet.write(row, 2, str(produit.categorie) if produit.categorie else "")
        worksheet.write(row, 3, produit.quantite_stock)
        worksheet.write(row, 4, produit.seuil_alerte)
        worksheet.write(row, 5, float(produit.prix_vente))
        worksheet.write(row, 6, float(produit.quantite_stock * produit.prix_vente))
    
    # Ajuster la largeur des colonnes
    worksheet.set_column('A:A', 15)  # Référence
    worksheet.set_column('B:B', 30)  # Désignation
    worksheet.set_column('C:C', 20)  # Catégorie
    worksheet.set_column('D:E', 15)  # Stock actuel, Seuil d'alerte
    worksheet.set_column('F:G', 15)  # Prix unitaire, Valeur totale
    
    # Fermer le classeur
    workbook.close()
    
    # Préparer la réponse
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=rapport_stock_faible.xlsx'
    
    return response

def rapport_mouvements(request):
    """
    Affiche un rapport des mouvements de stock (entrées et sorties) selon les filtres sélectionnés.
    """
    if not request.user.has_perm('stock.view_rapport_mouvements'):
        messages.error(request, _("Vous n'avez pas la permission d'accéder à ce rapport."))
        return redirect('stock:accueil')
    
    form = RapportMouvementsForm(request.GET or None)
    mouvements = []
    total_entrees = 0
    total_sorties = 0
    
    if form.is_valid():
        date_debut = form.cleaned_data.get('date_debut')
        date_fin = form.cleaned_data.get('date_fin')
        produit_id = form.cleaned_data.get('produit')
        type_mouvement = form.cleaned_data.get('type_mouvement')
        
        # Filtrer les entrées
        if type_mouvement in ['entree', 'tous']:
            entrees = EntreeStock.objects.filter(annulee=False)
            if date_debut:
                entrees = entrees.filter(date__gte=date_debut)
            if date_fin:
                # Ajouter un jour à la date de fin pour inclure toute la journée
                date_fin_plus_1 = date_fin + timedelta(days=1)
                entrees = entrees.filter(date__lt=date_fin_plus_1)
            if produit_id:
                entrees = entrees.filter(produit_id=produit_id)
            
            for entree in entrees:
                mouvements.append({
                    'type': 'entree',
                    'date': entree.date,
                    'reference': entree.reference,
                    'produit': entree.produit,
                    'quantite': entree.quantite,
                    'prix_unitaire': entree.prix_unitaire,
                    'montant_total': entree.quantite * entree.prix_unitaire,
                    'utilisateur': entree.utilisateur,
                    'notes': entree.notes,
                    'objet': entree
                })
                total_entrees += entree.quantite * entree.prix_unitaire
        
        # Filtrer les sorties
        if type_mouvement in ['sortie', 'tous']:
            sorties = SortieStock.objects.filter(annulee=False)
            if date_debut:
                sorties = sorties.filter(date__gte=date_debut)
            if date_fin:
                # Ajouter un jour à la date de fin pour inclure toute la journée
                date_fin_plus_1 = date_fin + timedelta(days=1)
                sorties = sorties.filter(date__lt=date_fin_plus_1)
            if produit_id:
                sorties = sorties.filter(produit_id=produit_id)
            
            for sortie in sorties:
                mouvements.append({
                    'type': 'sortie',
                    'date': sortie.date,
                    'reference': sortie.reference,
                    'produit': sortie.produit,
                    'quantite': sortie.quantite,
                    'prix_unitaire': sortie.prix_unitaire,
                    'montant_total': sortie.quantite * sortie.prix_unitaire,
                    'utilisateur': sortie.utilisateur,
                    'notes': sortie.notes,
                    'objet': sortie
                })
                total_sorties += sortie.quantite * sortie.prix_unitaire
        
        # Trier les mouvements par date (du plus récent au plus ancien)
        mouvements.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'title': _("Rapport des mouvements de stock"),
        'form': form,
        'mouvements': mouvements,
        'total_entrees': total_entrees,
        'total_sorties': total_sorties,
        'solde': total_entrees - total_sorties
    }
    
    return render(request, 'stock/rapports/mouvements.html', context)
