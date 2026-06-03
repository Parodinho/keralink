from django.db import models


class Voyageur(models.Model):
    nom               = models.CharField(max_length=100)
    prenom            = models.CharField(max_length=100)
    telephone         = models.CharField(max_length=20)
    pays_depart       = models.CharField(max_length=100)
    ville_depart      = models.CharField(max_length=100)
    pays_destination  = models.CharField(max_length=100)
    ville_destination = models.CharField(max_length=100)
    date_depart       = models.DateField()
    heure_depart      = models.TimeField()
    date_arrivee      = models.DateField()
    heure_arrivee     = models.TimeField()
    poids_disponible  = models.FloatField(default=0)
    TYPE_KG_CHOICES   = [
        ('entier', 'Kg en entier (tout ou rien)'),
        ('detail', 'Kg en détail (fractionnable)')
    ]
    type_kg           = models.CharField(max_length=10, choices=TYPE_KG_CHOICES, default='entier')
    guest_id          = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    is_matched        = models.BooleanField(default=False)
    is_created_via_matching = models.BooleanField(default=False)
    email             = models.EmailField(null=True, blank=True)
    note              = models.FloatField(default=5.0)
    STATUT_CHOICES    = [('actif', 'Actif'), ('complet', 'Complet'), ('termine', 'Terminé')]
    statut            = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    date_publication  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.ville_depart} → {self.ville_destination})"


class Expediteur(models.Model):
    nom               = models.CharField(max_length=100)
    prenom            = models.CharField(max_length=100)
    telephone         = models.CharField(max_length=20)
    pays              = models.CharField(max_length=100)
    ville             = models.CharField(max_length=100)
    pays_destination  = models.CharField(max_length=100)
    ville_destination = models.CharField(max_length=100)
    poids_colis       = models.FloatField()
    prix_total        = models.FloatField()
    commission        = models.FloatField(default=0)
    guest_id          = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    is_matched        = models.BooleanField(default=False)
    is_created_via_matching = models.BooleanField(default=False)
    email             = models.EmailField(null=True, blank=True)
    MODE_PAIEMENT     = [
        ('carte', 'Carte bancaire'), ('paypal', 'PayPal'),
        ('orange', 'Orange Money'),  ('wave', 'Wave')
    ]
    mode_paiement     = models.CharField(max_length=20, choices=MODE_PAIEMENT)
    paiement_effectue = models.BooleanField(default=False)
    reference_paiement = models.CharField(max_length=200, null=True, blank=True)
    date_paiement     = models.DateTimeField(null=True, blank=True)
    date_demande      = models.DateTimeField(auto_now_add=True)
    livraison_confirmee_expediteur = models.BooleanField(default=False)
    date_confirmation_expediteur   = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.poids_colis}kg"


class Matching(models.Model):
    expediteur = models.ForeignKey(Expediteur, on_delete=models.CASCADE, related_name='matchings')
    voyageur   = models.ForeignKey(Voyageur,   on_delete=models.CASCADE, related_name='matchings')
    STATUT_CHOICES = [
        ('en_attente', 'En attente'), ('confirme', 'Confirmé'),
        ('accepte', 'Accepté'),       ('refuse', 'Refusé'),
        ('livre', 'Livré'),
    ]
    statut                       = models.CharField(max_length=20, default="en_attente")
    livraison_confirmee_voyageur = models.BooleanField(default=False)
    photo_livraison              = models.ImageField(upload_to='livraisons/', null=True, blank=True)
    date_livraison               = models.DateTimeField(null=True, blank=True)
    date_creation                = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('expediteur', 'voyageur')

    def __str__(self):
        return f"Matching {self.expediteur} → {self.voyageur}"


class Demande(models.Model):
    expediteur = models.ForeignKey(Expediteur, on_delete=models.CASCADE)
    voyageur   = models.ForeignKey(Voyageur,   on_delete=models.CASCADE)
    statut     = models.CharField(max_length=20, choices=[
        ('en_attente', 'En attente'), ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),         ('termine', 'Terminé')
    ], default='en_attente')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_reponse  = models.DateTimeField(null=True, blank=True)


class Transaction(models.Model):
    expediteur         = models.ForeignKey(Expediteur, on_delete=models.CASCADE)
    voyageur           = models.ForeignKey(Voyageur,   on_delete=models.CASCADE,
                                           null=True, blank=True)
    montant            = models.FloatField()
    montant_voyageur   = models.FloatField(default=0)
    montant_commission = models.FloatField(default=0)
    mode_paiement      = models.CharField(max_length=20, choices=[
        ('carte', 'Carte bancaire'), ('paypal', 'PayPal'),
        ('orange', 'Orange Money'),  ('wave', 'Wave')
    ])
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('bloque', '🔒 Bloqué'),
        ('debloque', '✅ Débloqué vers voyageur'),
        ('rembourse', '↩️ Remboursé'),
        ('remboursement_demande', '🔴 Remboursement demandé'),
        ('echec', '❌ Échec'),
    ]
    statut             = models.CharField(max_length=30, choices=STATUT_CHOICES, default='en_attente')
    note_remboursement = models.TextField(null=True, blank=True)
    debloque_par       = models.CharField(max_length=200, null=True, blank=True)
    date_transaction   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.expediteur} — {self.montant}€ ({self.statut})"


class Message(models.Model):
    expediteur = models.ForeignKey(Expediteur, on_delete=models.CASCADE, null=True, blank=True)
    voyageur   = models.ForeignKey(Voyageur,   on_delete=models.CASCADE, null=True, blank=True)
    sender     = models.CharField(max_length=20, choices=[
        ('expediteur', 'Expéditeur'), ('voyageur', 'Voyageur')
    ])
    contenu             = models.TextField(blank=True)
    photo               = models.ImageField(upload_to='messages_photos/', null=True, blank=True)
    est_photo_livraison = models.BooleanField(default=False)
    date                = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"Message {self.sender} — {self.date.strftime('%d/%m %H:%M')}"


class MessageSupport(models.Model):
    guest_id    = models.CharField(max_length=100, db_index=True)
    nom_complet = models.CharField(max_length=200, default='Utilisateur')
    type_profil = models.CharField(max_length=20, default='inconnu')
    sender      = models.CharField(max_length=20, choices=[
        ('user', 'Utilisateur'), ('admin', 'Admin')
    ])
    contenu = models.TextField()
    lu      = models.BooleanField(default=False)
    date    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"Support [{self.sender}] {self.nom_complet} — {self.date.strftime('%d/%m %H:%M')}"


class Portefeuille(models.Model):
    # ✅ unique=True OK ici : un seul portefeuille par voyageur
    guest_id         = models.CharField(max_length=100, unique=True)
    nom_complet      = models.CharField(max_length=200, default='')
    solde            = models.FloatField(default=0)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Portefeuille {self.nom_complet} — {self.solde}€"


class Retrait(models.Model):
    guest_id    = models.CharField(max_length=100, db_index=True)
    nom_complet = models.CharField(max_length=200, default='')
    montant     = models.FloatField()
    MODE_CHOICES = [
        ('orange', 'Orange Money'), ('paypal', 'PayPal'),
        ('carte', 'Carte bancaire'), ('wave', 'Wave'),
        ('wise', 'Wise'), ('revolut', 'Revolut'),
        ('virement', 'Virement bancaire'),
    ]
    mode_retrait    = models.CharField(max_length=20, choices=MODE_CHOICES)
    coordonnees     = models.CharField(max_length=200)
    STATUT_CHOICES  = [
        ('en_attente', 'En attente'),
        ('traite', '✅ Traité'),
        ('refuse', '❌ Refusé'),
    ]
    statut          = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_demande    = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Retrait {self.nom_complet} — {self.montant}€ ({self.statut})"


class Profil(models.Model):
    TYPE_CHOICES  = [('voyageur', 'Voyageur'), ('expediteur', 'Expediteur')]
    type_profil   = models.CharField(max_length=20, choices=TYPE_CHOICES)
    nom_complet   = models.CharField(max_length=200)
    username      = models.CharField(max_length=100, unique=True)
    email         = models.EmailField()
    telephone     = models.CharField(max_length=20)
    password      = models.CharField(max_length=100)
    # ✅ unique=True UNIQUEMENT sur Profil — garanti car on génère
    # toujours un uuid4 frais dans creer_profil()
    # Les anciennes données doivent d'abord être nettoyées (voir procédure)
    guest_id      = models.CharField(max_length=100, unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom_complet} ({self.type_profil})"


class Visiteur(models.Model):
    guest_id             = models.CharField(max_length=100, unique=True)
    ip_address           = models.GenericIPAddressField(null=True, blank=True)
    date_premiere_visite = models.DateTimeField(auto_now_add=True)
    date_derniere_visite = models.DateTimeField(auto_now=True)
    nb_visites           = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Visiteur {self.guest_id[:8]}... ({self.nb_visites} visites)"

    @classmethod
    def total_visiteurs_uniques(cls):
        return cls.objects.count()