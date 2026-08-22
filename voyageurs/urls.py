from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Publication
    path('ajouter-voyageur/', views.ajouter_voyageur, name='ajouter_voyageur'),
    path('ajouter-expediteur/', views.ajouter_expediteur, name='ajouter_expediteur'),

    # ✅ Auth nouveau flux
    path('inscrire/', views.inscrire, name='inscrire'),
    path('login-profil/', views.login_profil, name='login_profil'),
    path('login/', views.page_login, name='page_login'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),

    # Compatibilité (ancienne page Profil → redirigée)
    path('creer-profil/', views.creer_profil, name='creer_profil'),
    path('creer-profil-page/', views.creer_profil_page, name='creer_profil_page'),

    # ✅ Vérification email (double opt-in)
    path('confirmer-email/<str:token>/', views.confirmer_email, name='confirmer_email'),
    path('renvoyer-confirmation-email/', views.renvoyer_confirmation_email, name='renvoyer_confirmation_email'),

    # ✅ Connexion / inscription via Google (repris en pause)
    # ⚠️ Le nom 'keralink_google_callback' est volontairement différent de
    # 'google_callback' : allauth utilise EN INTERNE ce nom exact pour sa
    # propre route technique /accounts/google/login/callback/. Réutiliser
    # le même nom ici crée une collision : reverse('google_callback')
    # résout alors vers NOTRE route (/google-callback/) au lieu de la
    # sienne, et allauth envoie donc la mauvaise redirect_uri à Google —
    # c'est exactement ce qui causait l'erreur redirect_uri_mismatch.
    path('continuer-avec-google/<str:type_profil>/', views.continuer_avec_google, name='continuer_avec_google'),
    path('google-callback/', views.google_callback, name='keralink_google_callback'),
    path('finaliser-profil-google/', views.finaliser_profil_google, name='finaliser_profil_google'),

    # Espace connecté & historique
    path('historique/', views.historique, name='historique'),
    path('espace-connecte/', views.espace_connecte, name='espace_connecte'),

    # Matching
    path('repondre-matching/', views.repondre_matching, name='repondre_matching'),
    path('accepter-demande/', views.accepter_demande, name='accepter_demande'),
    path('refuser-demande/', views.refuser_demande, name='refuser_demande'),
    path('creer-matching-apres-login/', views.creer_matching_apres_login, name='creer_matching_apres_login'),

    # Paiement
    path('paiement/', views.page_paiement, name='page_paiement'),
    path('traiter-paiement/', views.traiter_paiement, name='traiter_paiement'),
    path('debloquer-paiement/', views.debloquer_paiement, name='debloquer_paiement'),
    path('verifier-paiement/', views.verifier_paiement, name='verifier_paiement'),

    # Messages
    path('envoyer-message/', views.envoyer_message, name='envoyer_message'),
    path('get-messages/', views.get_messages, name='get_messages'),
    path('envoyer-message-support/', views.envoyer_message_support, name='envoyer_message_support'),
    path('get-messages-support/', views.get_messages_support, name='get_messages_support'),

    # Livraison / réception
    path('confirmer-livraison/', views.confirmer_livraison_voyageur, name='confirmer_livraison'),
    path('confirmer-reception/', views.confirmer_reception_expediteur, name='confirmer_reception'),

    # Portefeuille / retrait / remboursement
    path('get-portefeuille/', views.get_portefeuille, name='get_portefeuille'),
    path('demander-retrait/', views.demander_retrait, name='demander_retrait'),
    path('demander-remboursement/', views.demander_remboursement, name='demander_remboursement'),
    path('generer-facture-remboursement/<int:transaction_id>/', views.generer_facture_remboursement, name='generer_facture_remboursement'),

    # Infos trajet
    path('get-expediteur-info/', views.get_expediteur_info, name='get_expediteur_info'),
    path('get-voyageur-info/', views.get_voyageur_info, name='get_voyageur_info'),

    # Divers
    path('changer-langue/', views.changer_langue, name='changer_langue'),
    path('get-solde/', views.get_solde_temps_reel, name='get_solde'),
]