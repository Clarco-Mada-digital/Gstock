import os
import django

# Configurez les paramètres Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

# Créer un superutilisateur si aucun n'existe
def create_superuser():
    User = get_user_model()
    if not User.objects.filter(email='admin@example.com').exists():
        User.objects.create_superuser(
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User'
        )
        print("Superutilisateur créé avec succès!")
    else:
        print("Un superutilisateur avec cet email existe déjà.")

if __name__ == "__main__":
    create_superuser()
