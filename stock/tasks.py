from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Import différé pour éviter les imports circulaires
def get_notification_model():
    return apps.get_model('stock', 'Notification')

def get_produit_model():
    return apps.get_model('stock', 'Produit')

def get_user_model():
    return apps.get_model(settings.AUTH_USER_MODEL)

@shared_task
def verifier_stocks_bas():
    """
    Tâche périodique pour vérifier les stocks bas et générer des notifications.
    """
    # Importer les modèles de manière différée
    Notification = get_notification_model()
    Produit = get_produit_model()
    User = get_user_model()
    
    # Récupérer tous les administrateurs
    admins = User.objects.filter(is_staff=True)
    
    if not admins.exists():
        return "Aucun administrateur trouvé pour envoyer les notifications"
    
    # Récupérer les produits avec un stock en dessous du seuil d'alerte
    produits_en_alerte = Produit.objects.filter(
        quantite_stock__lte=models.F('seuil_alerte')
    )
    
    notifications_crees = 0
    
    for produit in produits_en_alerte:
        for admin in admins:
            # Vérifier si une notification similaire a déjà été créée récemment (dans les dernières 24h)
            derniere_notification = Notification.objects.filter(
                utilisateur=admin,
                message__icontains=produit.designation,
                date_creation__gte=timezone.now() - timezone.timedelta(hours=24)
            ).first()
            
            if not derniere_notification:
                if produit.quantite_stock == 0:
                    # Créer une notification de rupture de stock
                    message = _(
                        f"Rupture de stock pour {produit.designation}. "
                        "Veuillez réapprovisionner."
                    )
                    Notification.objects.create(
                        utilisateur=admin,
                        message=message,
                        niveau='danger',
                        lien=f"/stock/produits/{produit.id}/"
                    )
                else:
                    # Créer une notification de stock bas
                    message = _(
                        f"Stock bas pour {produit.designation}. "
                        f"Quantité restante : {produit.quantite_stock} (Seuil : {produit.seuil_alerte})"
                    )
                    Notification.objects.create(
                        utilisateur=admin,
                        message=message,
                        niveau='warning',
                        lien=f"/stock/produits/{produit.id}/"
                    )
                notifications_crees += 1
    
    return f"{notifications_crees} notifications de stock bas créées"
