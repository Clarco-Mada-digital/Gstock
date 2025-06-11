from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from stock.models import Categorie, Fournisseur, Produit, EntreeStock, SortieStock
from django.utils import timezone
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Crée des données de test pour l\'application de gestion de stock'

    def handle(self, *args, **options):
        # Créer un superutilisateur s'il n'existe pas
        if not User.objects.filter(email='admin@example.com').exists():
            User.objects.create_superuser(
                email='admin@example.com',
                password='admin123',
                telephone='+221 77 123 45 67',
                adresse='123 Admin Street',
                first_name='Admin',
                last_name='System'
            )
            self.stdout.write(self.style.SUCCESS('Superutilisateur créé avec succès!'))

        # Créer des catégories
        categories = []
        noms_categories = ['Électronique', 'Bureautique', 'Informatique', 'Mobilier', 'Fournitures']
        
        for nom in noms_categories:
            categorie, created = Categorie.objects.get_or_create(
                nom=nom,
                defaults={'description': f'Catégorie pour les produits de type {nom}'}
            )
            categories.append(categorie)  # Ajouter la catégorie même si elle existe déjà
            if created:
                self.stdout.write(f'Catégorie créée: {categorie.nom}')
            else:
                self.stdout.write(f'Catégorie existante récupérée: {categorie.nom}')

        # Créer des fournisseurs
        fournisseurs = []
        noms_fournisseurs = [
            'Fournisseur Pro', 'Tech Import', 'Bureau & Co',
            'Mega Stock', 'Global Distri', 'Office Plus'
        ]
        
        for nom in noms_fournisseurs:
            email = f'contact@{nom.lower().replace(" ", "")}.com'
            try:
                fournisseur, created = Fournisseur.objects.get_or_create(
                    email=email,
                    defaults={
                        'nom': nom,
                        'adresse': f'Adresse {nom}, Dakar, Sénégal',
                        'telephone': f'+221 77 {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}',
                        'contact': f'Contact {nom.split()[-1]}'
                    }
                )
                fournisseurs.append(fournisseur)  # Ajouter même s'il existe déjà
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Fournisseur créé: {fournisseur.nom}'))
                else:
                    self.stdout.write(f'Fournisseur existant récupéré: {fournisseur.nom}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erreur lors de la création du fournisseur {nom}: {str(e)}'))
        
        # Afficher le nombre de fournisseurs récupérés
        self.stdout.write(f'Nombre total de fournisseurs: {len(fournisseurs)}')
        for f in fournisseurs:
            self.stdout.write(f'- {f.nom} ({f.email})')

        # Créer des produits
        produits = []
        produits_data = [
            {'designation': 'Ordinateur Portable', 'code': 'ORD-PORT-001', 'prix_achat': 450000, 'prix_vente': 550000, 'quantite': 15, 'seuil_alerte': 5},
            {'designation': 'Souris Sans Fil', 'code': 'SOUR-001', 'prix_achat': 15000, 'prix_vente': 25000, 'quantite': 50, 'seuil_alerte': 10},
            {'designation': 'Clavier Mécanique', 'code': 'CLAV-001', 'prix_achat': 25000, 'prix_vente': 40000, 'quantite': 30, 'seuil_alerte': 5},
            {'designation': 'Écran 24"', 'code': 'ECR-24-001', 'prix_achat': 120000, 'prix_vente': 150000, 'quantite': 12, 'seuil_alerte': 3},
            {'designation': 'Casque Audio', 'code': 'CASQ-001', 'prix_achat': 35000, 'prix_vente': 55000, 'quantite': 25, 'seuil_alerte': 5},
            {'designation': 'Imprimante Laser', 'code': 'IMP-LAS-001', 'prix_achat': 180000, 'prix_vente': 250000, 'quantite': 8, 'seuil_alerte': 2},
            {'designation': 'Câble HDMI', 'code': 'CAB-HDMI', 'prix_achat': 3000, 'prix_vente': 7000, 'quantite': 100, 'seuil_alerte': 20},
            {'designation': 'Disque Dur Externe 1To', 'code': 'DD-EXT-1TO', 'prix_achat': 45000, 'prix_vente': 65000, 'quantite': 20, 'seuil_alerte': 5},
        ]

        for data in produits_data:
            try:
                # S'assurer qu'on a des catégories et des fournisseurs
                if not categories or not fournisseurs:
                    self.stdout.write(self.style.ERROR('Catégories ou fournisseurs manquants'))
                    break
                    
                produit, created = Produit.objects.get_or_create(
                    code=data['code'],
                    defaults={
                        'designation': data['designation'],
                        'prix_achat': data['prix_achat'],
                        'prix_vente': data['prix_vente'],
                        'quantite_stock': data['quantite'],
                        'seuil_alerte': data['seuil_alerte'],
                        'description': f'Description pour {data["designation"]}',
                        'categorie': random.choice(categories),
                        'fournisseur': random.choice(fournisseurs)
                    }
                )
                produits.append(produit)  # Ajouter même s'il existe déjà
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Produit créé: {produit.designation}'))
                else:
                    self.stdout.write(f'Produit existant récupéré: {produit.designation}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erreur lors de la création du produit {data["designation"]}: {str(e)}'))
        
        # Afficher le nombre de produits récupérés
        self.stdout.write(f'Nombre total de produits: {len(produits)}')
        for p in produits:
            self.stdout.write(f'- {p.designation} (Stock: {p.quantite_stock})')

        # Créer des entrées de stock
        for _ in range(20):
            produit = random.choice(produits)
            quantite = random.randint(1, 10)
            EntreeStock.objects.create(
                produit=produit,
                quantite=quantite,
                prix_unitaire=produit.prix_achat,
                fournisseur=random.choice(fournisseurs),
                date=timezone.now() - timezone.timedelta(days=random.randint(1, 30)),
                notes=f'Entrée de {quantite} {produit.designation}'
            )

        # Créer des sorties de stock
        admin_user = User.objects.filter(is_superuser=True).first()
        for _ in range(15):
            produit = random.choice(produits)
            quantite = random.randint(1, 5)
            if produit.quantite_stock >= quantite:
                SortieStock.objects.create(
                    produit=produit,
                    quantite=quantite,
                    prix_unitaire=produit.prix_vente,
                    utilisateur=admin_user,
                    client=f'Client #{random.randint(1000, 9999)}',
                    reference=f'SORT-{random.randint(1000, 9999)}',
                    date=timezone.now() - timezone.timedelta(days=random.randint(1, 30)),
                    notes=f'Vente de {quantite} {produit.designation}'
                )

        self.stdout.write(self.style.SUCCESS('Données de test créées avec succès!'))
