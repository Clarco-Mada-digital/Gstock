# GPlus StockPilot

Application de gestion de stock complète développée avec Django et Tailwind CSS.

## Prérequis

- Python 3.8+
- pip (gestionnaire de paquets Python)
- Node.js et npm (pour Tailwind CSS)

## Installation

1. **Cloner le dépôt**
   ```bash
   git clone [URL_DU_DEPOT]
   cd Gstock
   ```

2. **Créer et activer un environnement virtuel**
   ```bash
   # Sur Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Sur macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer la base de données**
   ```bash
   python manage.py migrate
   ```

5. **Créer un superutilisateur**
   ```bash
   python manage.py createsuperuser
   ```

6. **Lancer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

7. **Accéder à l'application**
   - Interface d'administration : http://127.0.0.1:8000/admin/
   - Application : http://127.0.0.1:8000/

## Fonctionnalités

- Gestion des produits
- Gestion des catégories
- Gestion des fournisseurs
- Entrées en stock
- Sorties de stock
- Tableau de bord avec indicateurs clés

## Structure du projet

- `config/` : Configuration du projet Django
- `stock/` : Application principale de gestion de stock
- `templates/` : Templates HTML
- `static/` : Fichiers statiques (CSS, JS, images)

## Prochaines étapes

1. Configurer les URLs pour les formulaires d'entrée/sortie
2. Implémenter les vues API pour les appels AJAX
3. Ajouter des rapports et exports
4. Configurer la production (base de données, paramètres de sécurité, etc.)

## Licence

Ce projet est sous licence MIT.
