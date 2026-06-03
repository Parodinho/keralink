from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Matching


@receiver(post_save, sender=Matching)
def gerer_poids_voyageur(sender, instance, created, **kwargs):
    """
    ✅ Diminue le poids du voyageur UNIQUEMENT lors de l'acceptation (statut='accepte').
    - created=True → NE RIEN FAIRE (matching vient d'être créé, pas encore accepté)
    - statut='accepte' → diminuer le poids du voyageur
    - statut='refuse' → ne rien faire, poids inchangé
    
    Utilise update() SQL direct pour éviter la récursion infinie du signal.
    """
    if created:
        return  # Matching créé → pas encore accepté

    if instance.statut != 'accepte':
        return  # Refus ou autre statut → poids inchangé

    voyageur = instance.voyageur
    expediteur = instance.expediteur
    poids_colis = expediteur.poids_colis

    VoyageurModel = voyageur.__class__

    if voyageur.type_kg == 'detail':
        # ✅ En détail : diminuer progressivement
        nouveau_poids = round(max(0.0, voyageur.poids_disponible - poids_colis), 2)
        if nouveau_poids <= 0:
            # Plus de poids → complet
            VoyageurModel.objects.filter(pk=voyageur.pk).update(
                poids_disponible=0.0,
                statut='complet',
                is_matched=True
            )
        else:
            # Encore du poids dispo → juste diminuer, annonce reste visible
            VoyageurModel.objects.filter(pk=voyageur.pk).update(
                poids_disponible=nouveau_poids
            )
    else:
        # ✅ En entier : tout ou rien → complet immédiatement
        VoyageurModel.objects.filter(pk=voyageur.pk).update(
            poids_disponible=0.0,
            statut='complet',
            is_matched=True
        )