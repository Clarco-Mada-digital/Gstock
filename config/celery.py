import os
from celery import Celery
from django.conf import settings

# Définit le module de paramètres par défaut pour l'application Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Utilisez une configuration d'objet Python pour éviter d'avoir à utiliser un séparateur de chaînes de caractères
app.config_from_object('django.conf:settings', namespace='CELERY')

# Charge les modules de tâches depuis toutes les applications Django enregistrées
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
