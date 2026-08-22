from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone, translation
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.urls import reverse
from django.db.models import Q, F
import uuid, random, string, base64, secrets
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required

# ✅ Vérification réelle d'existence d'email (format + résolution DNS/MX du domaine)
from email_validator import validate_email, EmailNotValidError

# ✅ Vérification réelle du numéro de téléphone (format + plage attribuée au pays)
import phonenumbers

from .models import (
    Voyageur, Expediteur, Matching, Profil,
    Demande, Transaction, Message, MessageSupport,
    Portefeuille, Retrait, Visiteur, COMMISSION_KERALINK
)
from voyageurs.tasks import (
    email_matching_expediteur,
    email_matching_voyageur,
    email_acceptation_expediteur,
    email_refus_expediteur,
    email_livraison_confirmee_expediteur,
    email_gains_debloques_voyageur,
    email_confirmation_reception_voyageur,
)


# ================================================================
# HELPERS
# ================================================================

def _get_profil_connecte(request):
    """Retourne le Profil connecté ou None. Plus de guest anonyme."""
    profil_id = request.session.get('profil_id')
    if not profil_id:
        return None
    return Profil.objects.filter(id=profil_id).first()


def _envoyer_email_confirmation(request, profil):
    """Génère un token unique et envoie l'email de confirmation d'adresse."""
    token = secrets.token_urlsafe(32)
    profil.token_verification_email = token
    profil.date_envoi_verification = timezone.now()
    profil.save(update_fields=['token_verification_email', 'date_envoi_verification'])

    lien = request.build_absolute_uri(reverse('confirmer_email', args=[token]))

    try:
        send_mail(
            subject="Confirmez votre adresse email — KERALINK",
            message=(
                f"Bonjour {profil.nom_complet},\n\n"
                "Merci de vous être inscrit sur KERALINK. Pour activer la publication "
                "d'annonces sur votre compte, merci de confirmer votre adresse email "
                f"en cliquant sur le lien suivant :\n\n{lien}\n\n"
                "Si vous n'êtes pas à l'origine de cette inscription, ignorez cet email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[profil.email],
            fail_silently=True,
        )
    except Exception:
        # Ne jamais bloquer l'inscription si l'envoi d'email échoue (SMTP down, etc.)
        pass


def _get_email_expediteur(expediteur):
    if expediteur.email and '@' in str(expediteur.email):
        return expediteur.email
    if expediteur.guest_id:
        profil = Profil.objects.filter(guest_id=expediteur.guest_id).first()
        if profil and profil.email and '@' in str(profil.email):
            Expediteur.objects.filter(pk=expediteur.pk).update(email=profil.email)
            return profil.email
    return None


def _get_email_voyageur(voyageur):
    if voyageur.email and '@' in str(voyageur.email):
        return voyageur.email
    if voyageur.guest_id:
        profil = Profil.objects.filter(guest_id=voyageur.guest_id).first()
        if profil and profil.email and '@' in str(profil.email):
            Voyageur.objects.filter(pk=voyageur.pk).update(email=profil.email)
            return profil.email
    return None


# ================================================================
# HOME
# ================================================================

def home(request):
    # Compteur visiteurs (optionnel, sans forcer un guest de publication)
    visitor_key = request.session.get('visitor_key')
    if not visitor_key:
        visitor_key = str(uuid.uuid4())
        request.session['visitor_key'] = visitor_key

    ip = (request.META.get('HTTP_X_FORWARDED_FOR', '') or '').split(',')[0].strip() \
         or request.META.get('REMOTE_ADDR', '')

    visiteur, cree = Visiteur.objects.get_or_create(
        guest_id=visitor_key,
        defaults={'ip_address': ip or None}
    )
    if not cree:
        Visiteur.objects.filter(guest_id=visitor_key).update(
            nb_visites=F('nb_visites') + 1,
            date_derniere_visite=timezone.now()
        )

    voyageurs = Voyageur.objects.filter(
        is_created_via_matching=False
    ).order_by('-date_publication')

    expediteurs = Expediteur.objects.filter(
        is_created_via_matching=False
    ).order_by('-date_demande')

    profil = _get_profil_connecte(request)

    return render(request, 'voyageurs/home.html', {
        'voyageurs':       voyageurs,
        'expediteurs':     expediteurs,
        'total_visiteurs': Visiteur.objects.count(),
        'profil_connecte': profil,
        'est_connecte':    profil is not None,
    })


def nb_visiteurs(request):
    return JsonResponse({'status': 'ok', 'total': Visiteur.objects.count()})


def historique(request):
    profil = _get_profil_connecte(request)
    transactions = []
    if profil:
        transactions = Transaction.objects.filter(
            expediteur__guest_id=profil.guest_id
        ).order_by('-date_transaction')
    return render(request, 'voyageurs/historique.html', {'transactions': transactions})


# ================================================================
# ✅ INSCRIPTION (crée l'ID unique) — 1ère fois
# Après succès → le front affiche le formulaire Expédier/Voyager
# ================================================================

@require_POST
def inscrire(request):
    try:
        nom       = request.POST.get('nom', '').strip()
        prenom    = request.POST.get('prenom', '').strip()
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        # type selon la page d'origine : expediteur | voyageur
        type_profil = request.POST.get('type_profil', '').strip().lower()
        if type_profil not in ('expediteur', 'voyageur'):
            return JsonResponse({'status': 'error', 'message': 'Type de compte invalide'})

        if not all([nom, prenom, username, email, password]):
            return JsonResponse({'status': 'error', 'message': 'Tous les champs sont obligatoires'})

        # ✅ Vérification réelle de l'email : format + le domaine doit réellement
        # exister et pouvoir recevoir des mails (résolution DNS/MX). Rejette les
        # domaines inventés ou mal orthographiés (ex: gmial.com, test.fake, etc.)
        try:
            email_verifie = validate_email(email, check_deliverability=True)
            email = email_verifie.normalized
        except EmailNotValidError:
            return JsonResponse({'status': 'error', 'message': "Adresse email incorrecte ou n'existe pas"})

        if password != password2:
            return JsonResponse({'status': 'error', 'message': 'Les mots de passe ne correspondent pas'})
        if len(password) < 4:
            return JsonResponse({'status': 'error', 'message': 'Mot de passe trop court'})
        if Profil.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': "Nom d'utilisateur déjà utilisé"})
        if Profil.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Email déjà utilisé'})
        if type_profil not in ('expediteur', 'voyageur'):
            type_profil = 'expediteur'

        # ✅ ID unique permanent créé UNIQUEMENT à l'inscription
        guest_id = str(uuid.uuid4())

        profil = Profil.objects.create(
            type_profil=type_profil,
            nom_complet=f"{prenom} {nom}".strip(),
            username=username,
            email=email,
            telephone=request.POST.get('telephone', ''),
            password=password,
            guest_id=guest_id,
        )

        # Session = compte connecté (plus de guest anonyme)
        request.session['profil_id'] = profil.id
        request.session['guest_id']  = guest_id  # conservé pour compatibilité matching/emails

        # Portefeuille vide pour les voyageurs
        if type_profil == 'voyageur':
            Portefeuille.objects.get_or_create(
                guest_id=guest_id,
                defaults={'nom_complet': profil.nom_complet, 'solde': 0.0}
            )

        # ✅ Envoi de l'email de confirmation (double opt-in) — le compte est
        # utilisable pour se connecter/pré-remplir, mais la publication reste
        # bloquée tant que l'email n'est pas confirmé (voir ajouter_expediteur
        # et ajouter_voyageur).
        _envoyer_email_confirmation(request, profil)

        return JsonResponse({
            'status':        'ok',
            'type_profil':   profil.type_profil,
            'nom_complet':   profil.nom_complet,
            'profil_id':     profil.id,
            'guest_id':      guest_id,
            'email_verifie': False,
            # front : afficher le formulaire Expédier ou Voyager (pas encore le dashboard)
            'action':        'show_form',
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ================================================================
# ✅ CONFIRMATION D'EMAIL (double opt-in)
# ================================================================

def confirmer_email(request, token):
    profil = Profil.objects.filter(token_verification_email=token).first()

    if not profil:
        titre, message, couleur = "Lien invalide", \
            "Ce lien de confirmation est invalide ou a déjà été utilisé.", "#c62828"
    else:
        profil.email_verifie = True
        profil.token_verification_email = None
        profil.save(update_fields=['email_verifie', 'token_verification_email'])
        titre, message, couleur = "Email confirmé ✅", \
            "Votre adresse email est confirmée. Vous pouvez maintenant publier vos annonces.", "#2e7d32"

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>{titre} — KERALINK</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5;
                    display: flex; align-items: center; justify-content: center;
                    min-height: 100vh; margin: 0; }}
            .card {{ background: white; border-radius: 16px; padding: 40px 32px;
                     max-width: 420px; text-align: center; box-shadow: 0 4px 24px rgba(0,0,0,0.1); }}
            h2 {{ color: {couleur}; margin-bottom: 12px; }}
            p {{ color: #555; font-size: 0.95rem; margin-bottom: 24px; }}
            a {{ display: inline-block; background: linear-gradient(90deg,#FF7A00,#e66900);
                 color: white; text-decoration: none; padding: 12px 28px;
                 border-radius: 8px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>{titre}</h2>
            <p>{message}</p>
            <a href="/">Retour à l'accueil</a>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)


@require_POST
def renvoyer_confirmation_email(request):
    profil = _get_profil_connecte(request)
    if not profil:
        return JsonResponse({'status': 'error', 'message': 'Vous devez être connecté', 'need_auth': True})
    if profil.email_verifie:
        return JsonResponse({'status': 'error', 'message': 'Votre email est déjà confirmé'})

    _envoyer_email_confirmation(request, profil)
    return JsonResponse({'status': 'ok', 'message': 'Email de confirmation renvoyé'})


# ================================================================
# ✅ CONNEXION (compte existant) → dashboard direct
# ================================================================

@require_POST
def login_profil(request):
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    type_attendu = request.POST.get('type_profil', '').strip().lower()  # expediteur | voyageur

    if not username or not password:
        return JsonResponse({'status': 'error', 'message': 'Identifiant et mot de passe requis'})

    profil = Profil.objects.filter(
        Q(username=username) | Q(email=username)
    ).first()

    if not profil or profil.password != password:
        return JsonResponse({'status': 'error', 'message': 'Informations incorrectes'})

    # ✅ Séparation stricte : page Expédier ≠ page Voyager
    if type_attendu and profil.type_profil != type_attendu:
        return JsonResponse({
            'status': 'error',
            'message': 'Informations incorrectes'  # volontairement générique
        })

    request.session['profil_id'] = profil.id
    request.session['guest_id'] = profil.guest_id

    return JsonResponse({
        'status': 'ok',
        'profil_id': profil.id,
        'guest_id': profil.guest_id,
        'type_profil': profil.type_profil,
        'nom_complet': profil.nom_complet,
        'telephone': profil.telephone or '',
        'redirect': '/espace-connecte/',
    })


def page_login(request):
    return render(request, 'voyageurs/login.html')


def deconnexion(request):
    request.session.flush()
    return redirect('/')


# ================================================================
# ✅ CONNEXION / INSCRIPTION VIA GOOGLE
# django-allauth gère l'échange OAuth avec Google et authentifie
# request.user (son propre modèle User). KERALINK utilise son propre
# modèle Profil, complètement séparé — ces 3 vues font le pont entre
# les deux : si un Profil existe déjà pour cet email Google, on
# connecte directement ; sinon on demande de finir l'inscription
# (nom, téléphone, mot de passe) sur completer_profil_google.html.
# ================================================================

def continuer_avec_google(request, type_profil):
    """Point de départ du bouton 'Continuer avec Google' : mémorise le
    type demandé (expéditeur/voyageur) avant de partir vers Google."""
    if type_profil not in ('expediteur', 'voyageur'):
        type_profil = 'expediteur'
    request.session['google_type_profil'] = type_profil
    return redirect('/accounts/google/login/?next=/google-callback/')


@login_required
def google_callback(request):
    """Arrivée après authentification Google réussie (allauth)."""
    google_user = request.user
    email = (google_user.email or '').strip().lower()
    type_demande = request.session.pop('google_type_profil', 'expediteur')

    if not email:
        return HttpResponse(
            "Impossible de récupérer votre email Google. Merci de réessayer "
            "ou de vous inscrire avec votre email directement."
        )

    profil = Profil.objects.filter(email__iexact=email).first()
    if profil:
        # ✅ Compte KERALINK déjà existant pour cet email → connexion directe,
        # même comportement que soumettreConnexion() : on affiche le
        # formulaire pré-rempli plutôt que le dashboard.
        request.session['profil_id'] = profil.id
        request.session['guest_id'] = profil.guest_id
        return redirect(f'/?open={profil.type_profil}')

    # ✅ Nouveau compte → finir l'inscription sur completer_profil_google.html
    nom_google = google_user.get_full_name() or google_user.username or ''
    request.session['google_pending_email'] = email
    request.session['google_pending_name'] = nom_google
    request.session['google_pending_type'] = type_demande

    return render(request, 'voyageurs/completer_profil_google.html', {
        'google_email': email,
        'google_name': nom_google,
        'type_defaut': type_demande,
    })


@require_POST
def finaliser_profil_google(request):
    """Traite le formulaire de completer_profil_google.html."""
    try:
        email = request.session.get('google_pending_email')
        if not email:
            return JsonResponse({
                'status': 'error',
                'message': "Session Google expirée, merci de recommencer via le bouton Google.",
            })

        type_profil = request.POST.get('type_profil', 'expediteur').strip().lower()
        if type_profil not in ('expediteur', 'voyageur'):
            type_profil = 'expediteur'

        nom_complet = request.POST.get('nom_complet', '').strip()
        username    = request.POST.get('username', '').strip()
        password    = request.POST.get('password', '')
        password2   = request.POST.get('password2', '')

        if not all([nom_complet, username, password]):
            return JsonResponse({'status': 'error', 'message': 'Tous les champs sont obligatoires'})
        if password != password2:
            return JsonResponse({'status': 'error', 'message': 'Les mots de passe ne correspondent pas'})
        if len(password) < 4:
            return JsonResponse({'status': 'error', 'message': 'Mot de passe trop court'})
        if Profil.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': "Nom d'utilisateur déjà utilisé"})
        if Profil.objects.filter(email__iexact=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Email déjà utilisé'})

        # ✅ Même contrôle réel de téléphone que le reste du site
        telephone_brut = request.POST.get('telephone', '')
        try:
            numero = phonenumbers.parse(telephone_brut, None)
            if not phonenumbers.is_valid_number(numero):
                raise ValueError
            telephone_verifie = phonenumbers.format_number(numero, phonenumbers.PhoneNumberFormat.E164)
        except (phonenumbers.NumberParseException, ValueError):
            return JsonResponse({'status': 'error', 'message': "Numéro de téléphone incorrect ou n'existe pas"})

        guest_id = str(uuid.uuid4())
        profil = Profil.objects.create(
            type_profil=type_profil,
            nom_complet=nom_complet,
            username=username,
            email=email,
            telephone=telephone_verifie,
            password=password,
            guest_id=guest_id,
            # ✅ Google a déjà vérifié cette adresse email : pas besoin de
            # notre propre email de confirmation ni d'attendre un clic.
            email_verifie=True,
        )

        request.session['profil_id'] = profil.id
        request.session['guest_id']  = guest_id
        request.session.pop('google_pending_email', None)
        request.session.pop('google_pending_name', None)
        request.session.pop('google_pending_type', None)

        if type_profil == 'voyageur':
            Portefeuille.objects.get_or_create(
                guest_id=guest_id,
                defaults={'nom_complet': nom_complet, 'solde': 0.0}
            )

        return JsonResponse({
            'status':      'ok',
            'type_profil': type_profil,
            'redirect':    f'/?open={type_profil}',
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# Ancienne page Profil → redirige vers accueil (supprimée)
def creer_profil_page(request):
    return redirect('/')


@require_POST
def creer_profil(request):
    """Compatibilité : redirige vers inscrire si encore appelée."""
    return inscrire(request)


# ================================================================
# ✅ AJOUTER EXPÉDITEUR — compte obligatoire
# ================================================================

@require_POST
def ajouter_expediteur(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({
                'status': 'error',
                'message': 'Vous devez être connecté pour publier',
                'need_auth': True,
            })
        if not profil.email_verifie:
            return JsonResponse({
                'status': 'error',
                'message': "Merci de confirmer votre adresse email avant de publier "
                           "(vérifiez votre boîte de réception, y compris les spams).",
                'email_non_verifie': True,
            })

        mode  = request.POST.get('mode', 'normal')
        poids = float(request.POST.get('poids'))
        prix_par_kg   = float(request.POST.get('prix_par_kg', 10.0))
        prix_total    = round(poids * prix_par_kg, 2)
        montant_total = round(prix_total + COMMISSION_KERALINK, 2)

        guest_id = profil.guest_id

        # ✅ Vérification réelle du numéro de téléphone : format + plage
        # réellement attribuée aux opérateurs du pays concerné (rejette les
        # numéros trop courts, mal formés ou inventés).
        telephone_brut = request.POST.get('telephone', profil.telephone or '')
        try:
            numero = phonenumbers.parse(telephone_brut, None)
            if not phonenumbers.is_valid_number(numero):
                raise ValueError
            telephone_verifie = phonenumbers.format_number(numero, phonenumbers.PhoneNumberFormat.E164)
        except (phonenumbers.NumberParseException, ValueError):
            return JsonResponse({'status': 'error', 'message': "Numéro de téléphone incorrect ou n'existe pas"})

        expediteur = Expediteur.objects.create(
            nom=request.POST.get('nom') or profil.nom_complet.split()[-1],
            prenom=request.POST.get('prenom') or profil.nom_complet.split()[0],
            telephone=telephone_verifie,
            pays=request.POST.get('pays'),
            ville=request.POST.get('ville'),
            pays_destination=request.POST.get('pays_destination'),
            ville_destination=request.POST.get('ville_destination'),
            poids_colis=poids,
            prix_par_kg=prix_par_kg,
            prix_total=prix_total,
            commission=COMMISSION_KERALINK,
            mode_paiement=request.POST.get('mode_paiement', 'carte'),
            guest_id=guest_id,
            is_matched=False,
            is_created_via_matching=(mode == 'matching'),
            paiement_effectue=False,
            email=profil.email,
        )

        if mode == 'matching':
            voyageur_id = request.POST.get('voyageur_id')
            voyageur = Voyageur.objects.get(id=voyageur_id)
            Matching.objects.get_or_create(
                expediteur=expediteur,
                voyageur=voyageur,
                defaults={'statut': 'en_attente'}
            )
            email_voy = _get_email_voyageur(voyageur)
            if email_voy:
                email_matching_voyageur(
                    email_voy,
                    f"{voyageur.prenom} {voyageur.nom}",
                    f"{expediteur.prenom} {expediteur.nom}",
                    expediteur.ville,
                    expediteur.ville_destination,
                    poids
                )

        return JsonResponse({
            'status':        'ok',
            'expediteur_id': expediteur.id,
            'montant_total': montant_total,
            # après publication → dashboard
            'redirect':      '/espace-connecte/',
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ================================================================
# ✅ AJOUTER VOYAGEUR — compte obligatoire
# ================================================================

@require_POST
def ajouter_voyageur(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({
                'status': 'error',
                'message': 'Vous devez être connecté pour publier',
                'need_auth': True,
            })
        if not profil.email_verifie:
            return JsonResponse({
                'status': 'error',
                'message': "Merci de confirmer votre adresse email avant de publier "
                           "(vérifiez votre boîte de réception, y compris les spams).",
                'email_non_verifie': True,
            })

        mode = request.POST.get('mode', 'normal')
        guest_id = profil.guest_id
        prix_par_kg = float(request.POST.get('prix_par_kg', 10.0))

        # ✅ Contrôle de chronologie côté serveur (ne jamais faire confiance
        # au seul contrôle navigateur, contournable) — l'arrivée doit être
        # strictement postérieure au départ.
        date_depart_str   = request.POST.get('date_depart')
        heure_depart_str  = request.POST.get('heure_depart')
        date_arrivee_str  = request.POST.get('date_arrivee')
        heure_arrivee_str = request.POST.get('heure_arrivee')

        try:
            depart_dt  = datetime.strptime(f"{date_depart_str} {heure_depart_str}", "%Y-%m-%d %H:%M")
            arrivee_dt = datetime.strptime(f"{date_arrivee_str} {heure_arrivee_str}", "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return JsonResponse({
                'status': 'error',
                'message': "Date ou heure de départ/arrivée invalide.",
            })

        if arrivee_dt <= depart_dt:
            return JsonResponse({
                'status': 'error',
                'message': "La date/heure d'arrivée doit être postérieure à la date/heure de départ.",
            })

        # ✅ Vérification réelle du numéro de téléphone (même contrôle que
        # pour l'expéditeur : format + plage réellement attribuée au pays).
        telephone_brut = request.POST.get('telephone', profil.telephone or '')
        try:
            numero = phonenumbers.parse(telephone_brut, None)
            if not phonenumbers.is_valid_number(numero):
                raise ValueError
            telephone_verifie = phonenumbers.format_number(numero, phonenumbers.PhoneNumberFormat.E164)
        except (phonenumbers.NumberParseException, ValueError):
            return JsonResponse({'status': 'error', 'message': "Numéro de téléphone incorrect ou n'existe pas"})

        voyageur = Voyageur.objects.create(
            nom=request.POST.get('nom') or profil.nom_complet.split()[-1],
            prenom=request.POST.get('prenom') or profil.nom_complet.split()[0],
            telephone=telephone_verifie,
            pays_depart=request.POST.get('pays_depart'),
            ville_depart=request.POST.get('ville_depart'),
            pays_destination=request.POST.get('pays_destination'),
            ville_destination=request.POST.get('ville_destination'),
            date_depart=request.POST.get('date_depart'),
            heure_depart=request.POST.get('heure_depart'),
            date_arrivee=request.POST.get('date_arrivee'),
            heure_arrivee=request.POST.get('heure_arrivee'),
            poids_disponible=float(request.POST.get('poids')),
            prix_par_kg=prix_par_kg,
            type_kg=request.POST.get('type_kg', 'entier'),
            guest_id=guest_id,
            is_matched=False,
            is_created_via_matching=(mode == 'matching'),
            email=profil.email,
        )

        if mode == 'matching':
            expediteur_id = request.POST.get('expediteur_id')
            expediteur = Expediteur.objects.get(id=expediteur_id)
            Matching.objects.get_or_create(
                expediteur=expediteur,
                voyageur=voyageur,
                defaults={'statut': 'en_attente'}
            )
            email_exp = _get_email_expediteur(expediteur)
            if email_exp:
                email_matching_expediteur(
                    email_exp,
                    f"{expediteur.prenom} {expediteur.nom}",
                    f"{voyageur.prenom} {voyageur.nom}",
                    voyageur.ville_depart,
                    voyageur.ville_destination,
                    expediteur.poids_colis
                )

        return JsonResponse({
            'status':      'ok',
            'voyageur_id': voyageur.id,
            'redirect':    '/espace-connecte/',
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ================================================================
# PAIEMENT
# ================================================================

@require_POST
def traiter_paiement(request):
    try:
        expediteur_id = request.POST.get('expediteur_id')
        mode_paiement = request.POST.get('mode_paiement')
        montant       = float(request.POST.get('montant', 0))

        expediteur = Expediteur.objects.get(id=expediteur_id)
        reference  = 'KRL-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        expediteur.paiement_effectue  = True
        expediteur.reference_paiement = reference
        expediteur.date_paiement      = timezone.now()
        expediteur.save()

        matching = expediteur.matchings.first()
        voyageur = matching.voyageur if matching else None

        montant_voyageur   = expediteur.prix_total
        montant_commission = COMMISSION_KERALINK

        Transaction.objects.create(
            expediteur=expediteur,
            voyageur=voyageur,
            montant=montant,
            montant_voyageur=montant_voyageur,
            montant_commission=montant_commission,
            mode_paiement=mode_paiement,
            statut='bloque'
        )

        profil = _get_profil_connecte(request)

        return JsonResponse({
            'status':       'ok',
            'reference':    reference,
            'has_matching': matching is not None,
            'has_profil':   profil is not None,
            'redirect':     '/espace-connecte/',
            'message':      f'Paiement de {montant}€ sécurisé ✅',
            'facture': {
                'reference':          reference,
                'nom':                f"{expediteur.prenom} {expediteur.nom}",
                'montant':            montant,
                'montant_voyageur':   montant_voyageur,
                'montant_commission': montant_commission,
                'prix_par_kg':        expediteur.prix_par_kg,
                'mode_paiement':      mode_paiement,
                'trajet':             f"{expediteur.ville} → {expediteur.ville_destination}",
                'poids':              expediteur.poids_colis,
                'date':               timezone.now().strftime('%d/%m/%Y à %H:%M'),
                'expediteur_id':      expediteur.id,
            }
        })
    except Expediteur.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Expéditeur introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def get_voyageur_info(request):
    try:
        v = Voyageur.objects.get(id=request.GET.get('voyageur_id'))
        return JsonResponse({
            'status': 'ok',
            'poids_disponible': v.poids_disponible,
            'prix_par_kg': v.prix_par_kg,
            'ville_depart': v.ville_depart,
            'pays_depart': v.pays_depart,
            'ville_destination': v.ville_destination,
            'pays_destination': v.pays_destination,
            'type_kg': v.type_kg,
        })
    except Voyageur.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Voyageur introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def get_expediteur_info(request):
    try:
        exp = Expediteur.objects.get(id=request.GET.get('expediteur_id'))
        return JsonResponse({
            'status': 'ok',
            'pays_depart': exp.pays,
            'ville_depart': exp.ville,
            'pays_destination': exp.pays_destination,
            'ville_destination': exp.ville_destination,
            'poids': exp.poids_colis,
            'prix_par_kg': exp.prix_par_kg,
        })
    except Expediteur.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Expéditeur introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ================================================================
# ESPACE CONNECTÉ (dashboard)
# ================================================================

def espace_connecte(request):
    profil = _get_profil_connecte(request)
    if not profil:
        return redirect('/login/')

    guest_id = profil.guest_id
    type_profil = profil.type_profil

    matchings = Matching.objects.filter(
        Q(expediteur__guest_id=guest_id) | Q(voyageur__guest_id=guest_id)
    ).select_related('expediteur', 'voyageur').order_by('-date_creation')

    demandes_en_attente = []
    if type_profil == 'voyageur':
        demandes_en_attente = Matching.objects.filter(
            voyageur__guest_id=guest_id,
            statut='en_attente'
        ).select_related('expediteur', 'voyageur')

    portefeuille = Portefeuille.objects.filter(guest_id=guest_id).first()
    solde_actuel = portefeuille.solde if portefeuille else 0.0

    # ✅ Transactions bloquées = remboursables pour l'expéditeur
    transactions_bloquees = Transaction.objects.filter(
        expediteur__guest_id=guest_id, statut='bloque'
    )

    # ✅ Transactions remboursables = alias explicite pour le template
    transactions_remboursables = transactions_bloquees

    transactions_debloquees = Transaction.objects.filter(
        voyageur__guest_id=guest_id, statut='debloque'
    ).order_by('-date_transaction')[:10]

    retraits_effectues = Retrait.objects.filter(
        guest_id=guest_id
    ).order_by('-date_demande')[:10]

    matchings_livres = matchings.filter(statut='livre')

    # ✅ Compteur "Confirmés" (expéditeur) — matchings acceptés par le voyageur
    matchings_confirmes = matchings.filter(statut='accepte').count()

    # ✅ Compteur "Publications" — nombre d'annonces publiées par ce compte
    # (une nouvelle ligne Expediteur/Voyageur est créée à chaque publication)
    if type_profil == 'expediteur':
        nb_publications = Expediteur.objects.filter(guest_id=guest_id).count()
    else:
        nb_publications = Voyageur.objects.filter(guest_id=guest_id).count()

    # ✅ Chat disponible si paiement effectué ET matching accepté ou livré
    if type_profil == 'expediteur':
        matchings_avec_chat = matchings.filter(
            statut__in=['accepte', 'livre'],
            expediteur__paiement_effectue=True
        )
    else:
        # Voyageur : chat disponible dès que matching accepté
        matchings_avec_chat = matchings.filter(
            statut__in=['accepte', 'livre']
        )

    # ✅ Messages support filtrés par guest_id
    messages_support = MessageSupport.objects.filter(
        guest_id=guest_id
    ).order_by('date')

    return render(request, 'voyageurs/espace_connecte.html', {
        'profil':                    profil,
        'type_profil':               type_profil,
        'nom_complet':               profil.nom_complet,
        'nom_initiale':              (profil.nom_complet[:1] or '?').upper(),
        'telephone':                 profil.telephone or '',
        'profil_id':                 profil.id,
        'matchings':                 matchings,
        'matchings_avec_chat':       matchings_avec_chat,
        'demandes_en_attente':       demandes_en_attente,
        'guest_id':                  guest_id,
        'solde_actuel':              solde_actuel,
        'portefeuille':              portefeuille,
        'transactions_bloquees':     transactions_bloquees,
        'transactions_remboursables': transactions_remboursables,
        'transactions_debloquees':   transactions_debloquees,
        'retraits_effectues':        retraits_effectues,
        'matchings_livres':          matchings_livres,
        'matchings_confirmes':       matchings_confirmes,
        'nb_publications':           nb_publications,
        'messages_support':          messages_support,
    })


# ================================================================
# RÉCEPTION / LIVRAISON / MATCHING
# ================================================================

@require_POST
def confirmer_reception_expediteur(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        matching_id = request.POST.get('matching_id')
        matching = Matching.objects.get(id=matching_id, expediteur__guest_id=profil.guest_id)

        matching.expediteur.livraison_confirmee_expediteur = True
        matching.expediteur.date_confirmation_expediteur   = timezone.now()
        matching.expediteur.save()

        transaction = Transaction.objects.filter(
            expediteur=matching.expediteur, statut='bloque'
        ).first()

        nom_expediteur = f"{matching.expediteur.prenom} {matching.expediteur.nom}"

        if transaction:
            transaction.statut      = 'debloque'
            transaction.debloque_par = nom_expediteur
            transaction.save()

            voyageur = matching.voyageur
            if transaction.voyageur is None and voyageur:
                transaction.voyageur = voyageur
                transaction.save()

            if voyageur and voyageur.guest_id:
                portefeuille, _ = Portefeuille.objects.get_or_create(
                    guest_id=voyageur.guest_id,
                    defaults={
                        'nom_complet': f"{voyageur.prenom} {voyageur.nom}",
                        'solde': 0.0
                    }
                )
                portefeuille.solde = round(portefeuille.solde + transaction.montant_voyageur, 2)
                portefeuille.save()

                email_voy = _get_email_voyageur(voyageur)
                if email_voy:
                    email_confirmation_reception_voyageur(
                        email_voy,
                        f"{voyageur.prenom} {voyageur.nom}",
                        nom_expediteur,
                        transaction.montant_voyageur,
                        matching.expediteur.ville,
                        matching.expediteur.ville_destination
                    )

        return JsonResponse({
            'status': 'ok',
            'message': 'Réception confirmée ✅ Gains débloqués vers le voyageur.'
        })
    except Matching.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Matching introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def repondre_matching(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        matching_id = request.POST.get('matching_id')
        decision    = request.POST.get('decision')  # accepte | refuse

        matching = Matching.objects.get(
            id=matching_id,
            voyageur__guest_id=profil.guest_id
        )

        nom_exp = f"{matching.expediteur.prenom} {matching.expediteur.nom}"
        nom_voy = f"{matching.voyageur.prenom} {matching.voyageur.nom}"
        ville_dep  = matching.expediteur.ville
        ville_dest = matching.expediteur.ville_destination
        email_exp  = _get_email_expediteur(matching.expediteur)

        if decision == 'accepte':
            matching.statut = 'accepte'
            matching.save()

            # Diminution kg gérée par signals.py à l'acceptation
            matching.expediteur.is_matched = True
            matching.expediteur.save()

            if email_exp:
                email_acceptation_expediteur(email_exp, nom_exp, nom_voy, ville_dep, ville_dest)
        else:
            matching.statut = 'refuse'
            matching.save()
            if email_exp:
                email_refus_expediteur(email_exp, nom_exp, nom_voy, ville_dep, ville_dest)

        return JsonResponse({'status': 'ok'})
    except Matching.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Matching introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def envoyer_message(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        matching_id = request.POST.get('matching_id')
        contenu     = request.POST.get('contenu', '').strip()
        guest_id    = profil.guest_id
        matching    = Matching.objects.get(id=matching_id)

        is_exp = (matching.expediteur.guest_id == guest_id)
        is_voy = (matching.voyageur.guest_id == guest_id)
        if not is_exp and not is_voy:
            return JsonResponse({'status': 'error', 'message': 'Accès refusé'})

        sender = 'expediteur' if is_exp else 'voyageur'
        message = Message(
            expediteur=matching.expediteur,
            voyageur=matching.voyageur,
            sender=sender,
            contenu=contenu
        )
        if 'photo' in request.FILES:
            message.photo = request.FILES['photo']
            message.est_photo_livraison = request.POST.get('est_livraison', 'false') == 'true'
        message.save()

        return JsonResponse({
            'status': 'ok',
            'message_id': message.id,
            'date': message.date.strftime('%H:%M'),
            'has_photo': bool(message.photo),
            'photo_url': message.photo.url if message.photo else None,
            'est_photo_livraison': message.est_photo_livraison,
            'sender': sender,
        })
    except Matching.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Matching introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def get_messages(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        matching_id = request.GET.get('matching_id')
        since_id    = int(request.GET.get('since_id', 0))
        guest_id    = profil.guest_id
        matching    = Matching.objects.get(id=matching_id)

        is_exp = (matching.expediteur.guest_id == guest_id)
        is_voy = (matching.voyageur.guest_id == guest_id)
        if not is_exp and not is_voy:
            return JsonResponse({'status': 'error', 'message': 'Accès refusé'})

        mon_role = 'expediteur' if is_exp else 'voyageur'
        messages = Message.objects.filter(
            expediteur=matching.expediteur,
            voyageur=matching.voyageur,
            id__gt=since_id
        ).order_by('date')

        data = [{
            'id': m.id,
            'sender': m.sender,
            'contenu': m.contenu,
            'date': m.date.strftime('%H:%M'),
            'is_mine': (m.sender == mon_role),
            'has_photo': bool(m.photo),
            'photo_url': m.photo.url if m.photo else None,
            'est_photo_livraison': m.est_photo_livraison,
        } for m in messages]
        return JsonResponse({'status': 'ok', 'messages': data, 'mon_role': mon_role})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def envoyer_message_support(request):
    try:
        contenu = request.POST.get('contenu', '').strip()
        if not contenu:
            return JsonResponse({'status': 'error', 'message': 'Message vide'})
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        msg = MessageSupport.objects.create(
            guest_id=profil.guest_id,
            nom_complet=profil.nom_complet,
            type_profil=profil.type_profil,
            sender='user',
            contenu=contenu
        )
        return JsonResponse({
            'status': 'ok',
            'message_id': msg.id,
            'contenu': contenu,
            'date': msg.date.strftime('%H:%M')
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def get_messages_support(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        since_id = int(request.GET.get('since_id', 0))
        messages = MessageSupport.objects.filter(
            guest_id=profil.guest_id, id__gt=since_id
        ).order_by('date')
        MessageSupport.objects.filter(
            guest_id=profil.guest_id, sender='admin', lu=False
        ).update(lu=True)
        data = [{
            'id': m.id, 'sender': m.sender, 'contenu': m.contenu,
            'date': m.date.strftime('%H:%M'), 'is_mine': m.sender == 'user'
        } for m in messages]
        return JsonResponse({'status': 'ok', 'messages': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def confirmer_livraison_voyageur(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        matching_id   = request.POST.get('matching_id')
        photo_base64  = request.POST.get('photo_base64', '').strip()
        photo_fichier = request.FILES.get('photo')

        if not photo_base64 and not photo_fichier:
            return JsonResponse({'status': 'error', 'message': 'La photo est obligatoire'})

        matching = Matching.objects.get(id=matching_id, voyageur__guest_id=profil.guest_id)

        if photo_base64:
            try:
                if ';base64,' in photo_base64:
                    format_part, imgstr = photo_base64.split(';base64,')
                    ext = format_part.split('/')[-1]
                    if ext not in ['jpeg', 'jpg', 'png', 'webp']:
                        ext = 'jpg'
                else:
                    imgstr = photo_base64
                    ext = 'jpg'
                photo_data = base64.b64decode(imgstr)
                photo_file = ContentFile(photo_data, name=f'livraison_{matching.id}.{ext}')
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': 'Format photo invalide : ' + str(e)})
        else:
            photo_file = photo_fichier

        matching.livraison_confirmee_voyageur = True
        matching.date_livraison = timezone.now()
        matching.statut = 'livre'
        matching.photo_livraison = photo_file
        matching.save()

        Message.objects.create(
            expediteur=matching.expediteur,
            voyageur=matching.voyageur,
            sender='voyageur',
            contenu='📦 Photo de confirmation de livraison',
            photo=photo_file,
            est_photo_livraison=True
        )

        email_exp = _get_email_expediteur(matching.expediteur)
        if email_exp:
            email_livraison_confirmee_expediteur(
                email_exp,
                f"{matching.expediteur.prenom} {matching.expediteur.nom}",
                f"{matching.voyageur.prenom} {matching.voyageur.nom}",
                matching.expediteur.ville,
                matching.expediteur.ville_destination
            )

        return JsonResponse({
            'status': 'ok',
            'message': "Livraison confirmée ✅. Photo envoyée à l'expéditeur."
        })
    except Matching.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Matching introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def debloquer_paiement_admin(request, transaction_id):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        if transaction.statut == 'bloque':
            transaction.statut = 'debloque'
            transaction.debloque_par = 'Admin KERALINK'
            transaction.save()
            voyageur = transaction.voyageur
            if not voyageur:
                matching = Matching.objects.filter(expediteur=transaction.expediteur).first()
                if matching:
                    voyageur = matching.voyageur
            if voyageur and voyageur.guest_id:
                portefeuille, _ = Portefeuille.objects.get_or_create(
                    guest_id=voyageur.guest_id,
                    defaults={'nom_complet': f"{voyageur.prenom} {voyageur.nom}"}
                )
                portefeuille.solde += transaction.montant_voyageur
                portefeuille.save()
                email_voy = _get_email_voyageur(voyageur)
                if email_voy:
                    email_gains_debloques_voyageur(
                        email_voy,
                        f"{voyageur.prenom} {voyageur.nom}",
                        transaction.montant_voyageur,
                        'Admin KERALINK',
                        transaction.expediteur.ville if transaction.expediteur else '',
                        transaction.expediteur.ville_destination if transaction.expediteur else ''
                    )
    except Transaction.DoesNotExist:
        pass
    return redirect('/admin/voyageurs/transaction/')


@require_POST
def debloquer_paiement(request):
    try:
        transaction = Transaction.objects.get(id=request.POST.get('transaction_id'))
        transaction.statut = 'debloque'
        transaction.save()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def demander_remboursement(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        transaction = Transaction.objects.get(
            id=request.POST.get('transaction_id'),
            expediteur__guest_id=profil.guest_id,
            statut='bloque'
        )
        transaction.statut = 'remboursement_demande'
        transaction.note_remboursement = request.POST.get('motif', 'Aucun voyageur trouvé')
        transaction.save()
        facture_url = reverse('generer_facture_remboursement', kwargs={'transaction_id': transaction.id})
        return JsonResponse({
            'status': 'ok',
            'message': 'Demande envoyée ✅. Traitement sous 48h.',
            'facture_url': facture_url,
        })
    except Transaction.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Transaction introuvable ou non éligible'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def rembourser_admin(request, transaction_id):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        transaction.statut = 'rembourse'
        transaction.save()
    except Transaction.DoesNotExist:
        pass
    return redirect('/admin/voyageurs/transaction/')


def get_portefeuille(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        portefeuille, _ = Portefeuille.objects.get_or_create(
            guest_id=profil.guest_id,
            defaults={'nom_complet': profil.nom_complet}
        )
        retraits = Retrait.objects.filter(guest_id=profil.guest_id).order_by('-date_demande')[:10]
        return JsonResponse({
            'status': 'ok',
            'solde': portefeuille.solde,
            'retraits': [{
                'montant': r.montant,
                'mode': r.mode_retrait,
                'coordonnees': r.coordonnees,
                'statut': r.statut,
                'date': r.date_demande.strftime('%d/%m/%Y à %H:%M')
            } for r in retraits]
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def demander_retrait(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        montant = float(request.POST.get('montant', 0))
        mode = request.POST.get('mode_retrait')
        coordonnees = request.POST.get('coordonnees', '').strip()
        if montant <= 0:
            return JsonResponse({'status': 'error', 'message': 'Montant invalide'})
        if not mode:
            return JsonResponse({'status': 'error', 'message': 'Mode de retrait requis'})
        if not coordonnees:
            return JsonResponse({'status': 'error', 'message': 'Coordonnées requises'})
        portefeuille = Portefeuille.objects.filter(guest_id=profil.guest_id).first()
        if not portefeuille or portefeuille.solde < montant:
            return JsonResponse({'status': 'error', 'message': 'Solde insuffisant'})
        portefeuille.solde -= montant
        portefeuille.save()
        Retrait.objects.create(
            guest_id=profil.guest_id,
            nom_complet=profil.nom_complet,
            montant=montant,
            mode_retrait=mode,
            coordonnees=coordonnees,
            statut='traite'
        )
        return JsonResponse({
            'status': 'ok',
            'message': f'Retrait de {montant:.2f}€ effectué ✅ — Envoi vers {coordonnees}',
            'nouveau_solde': portefeuille.solde
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def verifier_paiement(request):
    try:
        matching = Matching.objects.get(id=request.GET.get('matching_id'))
        nom = f"{matching.expediteur.prenom} {matching.expediteur.nom}"
        initiale = matching.expediteur.prenom[0].upper() if matching.expediteur.prenom else '?'
        return JsonResponse({
            'status': 'ok',
            'paiement_effectue': matching.expediteur.paiement_effectue,
            'expediteur_nom': nom,
            'expediteur_initiale': initiale
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def creer_matching_apres_login(request):
    try:
        profil = _get_profil_connecte(request)
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        type_match = request.POST.get('type')
        guest_id = profil.guest_id
        if type_match == 'voyageur':
            expediteur = Expediteur.objects.get(id=request.POST.get('expediteur_id'))
            voyageur = Voyageur.objects.filter(guest_id=guest_id).last()
            if not voyageur:
                return JsonResponse({'status': 'need_form', 'message': 'Remplir le formulaire'})
            Matching.objects.get_or_create(
                expediteur=expediteur, voyageur=voyageur,
                defaults={'statut': 'en_attente'}
            )
            expediteur.is_matched = True
            expediteur.save()
            return JsonResponse({'status': 'ok', 'redirect': '/espace-connecte/'})
        elif type_match == 'expediteur':
            voyageur = Voyageur.objects.get(id=request.POST.get('voyageur_id'))
            expediteur = Expediteur.objects.filter(guest_id=guest_id).last()
            if not expediteur:
                return JsonResponse({'status': 'need_form', 'message': 'Remplir le formulaire'})
            Matching.objects.get_or_create(
                expediteur=expediteur, voyageur=voyageur,
                defaults={'statut': 'en_attente'}
            )
            return JsonResponse({'status': 'ok', 'redirect': '/espace-connecte/'})
        return JsonResponse({'status': 'error', 'message': 'Type inconnu'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def traiter_retrait_admin(request, retrait_id):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    try:
        retrait = Retrait.objects.get(id=retrait_id)
        retrait.statut = 'traite'
        retrait.date_traitement = timezone.now()
        retrait.save()
    except Retrait.DoesNotExist:
        pass
    return redirect('/admin/voyageurs/retrait/')


def refuser_retrait_admin(request, retrait_id):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    try:
        retrait = Retrait.objects.get(id=retrait_id)
        portefeuille = Portefeuille.objects.filter(guest_id=retrait.guest_id).first()
        if portefeuille:
            portefeuille.solde += retrait.montant
            portefeuille.save()
        retrait.statut = 'refuse'
        retrait.date_traitement = timezone.now()
        retrait.save()
    except Retrait.DoesNotExist:
        pass
    return redirect('/admin/voyageurs/retrait/')


@require_POST
def accepter_demande(request):
    return repondre_matching(request)


@require_POST
def refuser_demande(request):
    # Adapter decision=refuse si le front envoie autrement
    if not request.POST.get('decision'):
        mutable = request.POST.copy()
        mutable['decision'] = 'refuse'
        request.POST = mutable
    return repondre_matching(request)


def get_solde_temps_reel(request):
    profil = _get_profil_connecte(request)
    if not profil:
        return JsonResponse({'status': 'error', 'message': 'Non connecté'})
    portefeuille = Portefeuille.objects.filter(guest_id=profil.guest_id).first()
    solde = portefeuille.solde if portefeuille else 0.0
    return JsonResponse({'status': 'ok', 'solde': solde})


def changer_langue(request):
    if request.method == 'POST':
        langue = request.POST.get('langue', 'fr')
        if langue in ['fr', 'en']:
            translation.activate(langue)
            request.session['_language'] = langue
            response = JsonResponse({'status': 'ok', 'langue': langue})
            response.set_cookie('django_language', langue)
            return response
    return JsonResponse({'status': 'error'})


def generer_facture_remboursement(request, transaction_id):
    try:
        transaction = get_object_or_404(Transaction, id=transaction_id)
        reference = transaction.expediteur.reference_paiement or f"KRL-PAI-{transaction.id}"
        context = {
            'reference': reference,
            'nom': f"{transaction.expediteur.prenom} {transaction.expediteur.nom}",
            'montant_paye': float(transaction.montant),
            'montant_rembourse': float(transaction.montant_voyageur),
            'montant_commission': float(transaction.montant_commission),
            'trajet': f"{transaction.expediteur.ville} → {transaction.expediteur.ville_destination}",
            'poids': float(transaction.expediteur.poids_colis),
            'prix_par_kg': float(transaction.expediteur.prix_par_kg),
            'date': timezone.now().strftime('%d/%m/%Y à %H:%M'),
        }
        html_content = render_to_string('voyageurs/facture_remboursement.html', context)
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="Facture_Remboursement_{reference}.html"'
        return response
    except Exception as e:
        return HttpResponse(f"Erreur : {str(e)}", status=500)

def page_paiement(request):
    expediteur_id = request.GET.get('expediteur_id', '')
    montant = request.GET.get('montant', '0')
    return render(request, 'voyageurs/paiement.html', {
        'expediteur_id': expediteur_id,
        'montant': montant,
    })


def completer_profil_google(request):
    return redirect('/')

def deconnexion(request):
    request.session.flush()
    return redirect('/')