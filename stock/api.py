from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import Produit
import json

@csrf_exempt
@require_http_methods(["GET"])
def get_produit_details(request, produit_id):
    """
    Vue API pour récupérer les détails d'un produit en JSON
    Utilisé pour les formulaires d'entrée/sortie
    """
    try:
        produit = get_object_or_404(Produit, id=produit_id)
        
        data = {
            'id': produit.id,
            'code': produit.code,
            'designation': produit.designation,
            'categorie': str(produit.categorie) if produit.categorie else None,
            'quantite_stock': produit.quantite_stock,
            'prix_achat': str(produit.prix_achat) if produit.prix_achat else '0.00',
            'prix_vente': str(produit.prix_vente) if produit.prix_vente else '0.00',
            'photo': produit.photo.url if produit.photo else None,
            'seuil_alerte': produit.seuil_alerte,
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
