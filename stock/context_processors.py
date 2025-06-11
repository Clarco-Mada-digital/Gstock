from stock.models import Notification

def notifications(request):
    """
    Ajoute les notifications non lues au contexte de tous les templates.
    """
    if not request.user.is_authenticated:
        return {}
        
    return {
        'unread_notifications_count': request.user.notifications.filter(vue=False).count(),
        'recent_notifications': request.user.notifications.all().order_by('-date_creation')[:5]
    }
