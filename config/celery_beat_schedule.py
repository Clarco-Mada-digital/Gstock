from celery.schedules import crontab

# Configuration de la planification des tâches périodiques
CELERY_BEAT_SCHEDULE = {
    'verifier-stocks-bas': {
        'task': 'stock.tasks.verifier_stocks_bas',
        'schedule': crontab(hour=9, minute=0),  # Tous les jours à 9h du matin
        'options': {'expires': 60 * 60},  # Expire après 1 heure
    },
}
