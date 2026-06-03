from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import uuid, random, string
from django.http import HttpResponse
import base64
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse

from .models import (Voyageur, Expediteur, Matching, Profil,
                     Demande, Transaction, Message, MessageSupport,
                     Portefeuille, Retrait, Visiteur)
from voyageurs.tasks import (
    email_matching_expediteur,
    email_matching_voyageur,
    email_acceptation_expediteur,
    email_refus_expediteur,
    # ✅ email_message_recu_* SUPPRIMÉS — notifications de message désactivées
    email_livraison_confirmee_expediteur,
    email_gains_debloques_voyageur,
    email_confirmation_reception_voyageur,
)


# ================================================================
# ✅ HELPERS EMAIL — version robuste
# ================================================================

def _get_email_expediteur(expediteur):
    """
    Récupère l'email de l'expéditeur avec fallback :
    1. Email stocké directement sur l'objet Expediteur
    2. Email du Profil avec le même guest_id
    """
    if expediteur.email and '@' in str(expediteur.email):
        print(f"[EMAIL ✅] Expéditeur {expediteur.prenom} {expediteur.nom} → email direct: {expediteur.email}")
        return expediteur.email

    if expediteur.guest_id:
        profil = Profil.objects.filter(guest_id=expediteur.guest_id).first()
        if profil and profil.email and '@' in str(profil.email):
            Expediteur.objects.filter(pk=expediteur.pk).update(email=profil.email)
            print(f"[EMAIL ✅] Expéditeur {expediteur.prenom} {expediteur.nom} → via profil: {profil.email}")
            return profil.email

    print(f"[EMAIL ❌] Aucun email pour expéditeur {expediteur.prenom} {expediteur.nom}")
    return None


def _get_email_voyageur(voyageur):
    """
    Récupère l'email du voyageur avec fallback :
    1. Email stocké directement sur l'objet Voyageur
    2. Email du Profil avec le même guest_id
    """
    if voyageur.email and '@' in str(voyageur.email):
        print(f"[EMAIL ✅] Voyageur {voyageur.prenom} {voyageur.nom} → email direct: {voyageur.email}")
        return voyageur.email

    if voyageur.guest_id:
        profil = Profil.objects.filter(guest_id=voyageur.guest_id).first()
        if profil and profil.email and '@' in str(profil.email):
            Voyageur.objects.filter(pk=voyageur.pk).update(email=profil.email)
            print(f"[EMAIL ✅] Voyageur {voyageur.prenom} {voyageur.nom} → via profil: {profil.email}")
            return profil.email

    print(f"[EMAIL ❌] Aucun email pour voyageur {voyageur.prenom} {voyageur.nom}")
    return None


def _get_email_profil(guest_id):
    """Récupère l'email depuis le guest_id (usage général)."""
    if not guest_id:
        return None
    profil = Profil.objects.filter(guest_id=guest_id).first()
    if profil and profil.email and '@' in str(profil.email):
        return profil.email
    return None


# ================================================================
# VUES PRINCIPALES
# ================================================================

# ================================================================
# 2. REMPLACEZ la fonction home dans views.py
# ================================================================

# ================================================================
# Remplacez la fonction home dans views.py
# ================================================================

def home(request):
    if not request.session.get('guest_id'):
        request.session['guest_id'] = str(uuid.uuid4())

    guest_id = request.session['guest_id']

    # ✅ IP de l'utilisateur
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
         or request.META.get('REMOTE_ADDR', '')

    visiteur, cree = Visiteur.objects.get_or_create(
        guest_id=guest_id,
        defaults={'ip_address': ip or None}
    )
    if not cree:
        # ✅ F() importé directement depuis django.db.models — pas besoin de "models."
        from django.db.models import F
        Visiteur.objects.filter(guest_id=guest_id).update(
            nb_visites=F('nb_visites') + 1,
            date_derniere_visite=timezone.now()
        )

    total_visiteurs = Visiteur.objects.count()

    voyageurs = Voyageur.objects.filter(
        is_created_via_matching=False
    ).order_by('-date_publication')

    expediteurs = Expediteur.objects.filter(
        is_created_via_matching=False
    ).order_by('-date_demande')

    return render(request, 'voyageurs/home.html', {
        'voyageurs':       voyageurs,
        'expediteurs':     expediteurs,
        'guest_id':        guest_id,
        'total_visiteurs': total_visiteurs,
    })


def historique(request):
    profil_id = request.session.get('profil_id')
    transactions = []
    if profil_id:
        profil = Profil.objects.filter(id=profil_id).first()
        if profil:
            # ✅ ISOLATION : filtrer strictement par guest_id du profil connecté
            transactions = Transaction.objects.filter(
                expediteur__guest_id=profil.guest_id
            ).order_by('-date_transaction')
    return render(request, 'voyageurs/historique.html', {'transactions': transactions})


@require_POST
def ajouter_expediteur(request):
    try:
        mode = request.POST.get('mode', 'normal')
        poids = float(request.POST.get('poids'))
        prix = float(request.POST.get('prix'))

        if mode == 'normal':
            nouveau_guest_id = str(uuid.uuid4())
            request.session['guest_id'] = nouveau_guest_id
            request.session['profil_id'] = None
            guest_id = nouveau_guest_id
        else:
            if not request.session.get('guest_id'):
                request.session['guest_id'] = str(uuid.uuid4())
            guest_id = request.session['guest_id']

        email_exp_connecte = None
        profil_id = request.session.get('profil_id')
        if profil_id:
            profil_connecte = Profil.objects.filter(id=profil_id).first()
            if profil_connecte:
                email_exp_connecte = profil_connecte.email

        expediteur = Expediteur.objects.create(
            nom=request.POST.get('nom'),
            prenom=request.POST.get('prenom'),
            telephone=request.POST.get('telephone'),
            pays=request.POST.get('pays'),
            ville=request.POST.get('ville'),
            pays_destination=request.POST.get('pays_destination'),
            ville_destination=request.POST.get('ville_destination'),
            poids_colis=poids,
            prix_total=prix,
            commission=poids * 0.2,
            mode_paiement=request.POST.get('mode_paiement'),
            guest_id=guest_id,
            is_matched=False,
            is_created_via_matching=(mode == 'matching'),
            paiement_effectue=False,
            email=email_exp_connecte,
        )

        if mode == 'matching':
            voyageur_id = request.POST.get('voyageur_id')
            voyageur = Voyageur.objects.get(id=voyageur_id)

            # 🔥 ISOLATION FIX
            expediteur.guest_id = guest_id
            expediteur.save()

            voyageur.guest_id = voyageur.guest_id or guest_id
            voyageur.save()

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

        return JsonResponse({'status': 'ok', 'expediteur_id': expediteur.id})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def ajouter_voyageur(request):
    try:
        mode = request.POST.get('mode', 'normal')

        if not request.session.get('guest_id'):
            request.session['guest_id'] = str(uuid.uuid4())

        guest_id = request.session['guest_id']

        email_voy_connecte = None
        profil_id = request.session.get('profil_id')
        if profil_id:
            profil_connecte = Profil.objects.filter(id=profil_id).first()
            if profil_connecte:
                email_voy_connecte = profil_connecte.email

        voyageur = Voyageur.objects.create(
            nom=request.POST.get('nom'),
            prenom=request.POST.get('prenom'),
            telephone=request.POST.get('telephone'),
            pays_depart=request.POST.get('pays_depart'),
            ville_depart=request.POST.get('ville_depart'),
            pays_destination=request.POST.get('pays_destination'),
            ville_destination=request.POST.get('ville_destination'),
            date_depart=request.POST.get('date_depart'),
            heure_depart=request.POST.get('heure_depart'),
            date_arrivee=request.POST.get('date_arrivee'),
            heure_arrivee=request.POST.get('heure_arrivee'),
            poids_disponible=float(request.POST.get('poids')),
            type_kg=request.POST.get('type_kg', 'entier'),
            guest_id=guest_id,
            is_matched=False,
            is_created_via_matching=(mode == 'matching'),
            email=email_voy_connecte,
        )

        if mode == 'matching':
            expediteur_id = request.POST.get('expediteur_id')
            expediteur = Expediteur.objects.get(id=expediteur_id)

            # 🔥 ISOLATION FIX
            voyageur.guest_id = guest_id
            voyageur.save()

            expediteur.guest_id = expediteur.guest_id or guest_id
            expediteur.save()

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

        return JsonResponse({'status': 'ok', 'voyageur_id': voyageur.id})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def nb_visiteurs(request):
    """Retourne le nombre total de visiteurs uniques (JSON)."""
    from .models import Visiteur
    total = Visiteur.objects.count()
    return JsonResponse({'status': 'ok', 'total': total})

# ================================================================
# CORRECTION ISOLATION — remplacez ces 2 fonctions dans views.py
# ================================================================

@require_POST
def creer_profil(request):
    try:
        username = request.POST.get('username', '').strip()
        if Profil.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Nom utilisateur déjà utilisé'})

        email = request.POST.get('email', '')
        expediteur_id = request.POST.get('expediteur_id')
        voyageur_id = request.POST.get('voyageur_id')

        # ✅ CAS 1 : le profil est lié à une annonce existante
        # → utiliser le guest_id de CETTE annonce (déjà créée avant l'inscription)
        if expediteur_id:
            try:
                exp = Expediteur.objects.get(id=expediteur_id)
                # Utiliser le guest_id de l'expéditeur existant s'il en a un
                # sinon générer un nouveau guest_id propre
                guest_id = exp.guest_id if exp.guest_id else str(uuid.uuid4())
            except Expediteur.DoesNotExist:
                guest_id = str(uuid.uuid4())

        elif voyageur_id:
            try:
                voy = Voyageur.objects.get(id=voyageur_id)
                guest_id = voy.guest_id if voy.guest_id else str(uuid.uuid4())
            except Voyageur.DoesNotExist:
                guest_id = str(uuid.uuid4())

        else:
            # ✅ CAS 2 : inscription sans annonce préalable (profil vierge)
            # → TOUJOURS générer un nouveau guest_id unique
            # NE PAS réutiliser le guest_id de session qui peut appartenir
            # à un autre expéditeur/voyageur déjà existant
            guest_id = str(uuid.uuid4())

        # Vérifier que ce guest_id n'est pas déjà utilisé par un autre profil
        # (sécurité supplémentaire)
        if Profil.objects.filter(guest_id=guest_id).exists():
            guest_id = str(uuid.uuid4())

        profil = Profil.objects.create(
            type_profil=request.POST.get('type_profil'),
            nom_complet=request.POST.get('nom_complet'),
            username=username,
            email=email,
            telephone=request.POST.get('telephone', ''),
            password=request.POST.get('password'),
            guest_id=guest_id
        )

        # Lier l'email aux annonces concernées
        if expediteur_id:
            Expediteur.objects.filter(id=expediteur_id).update(
                guest_id=guest_id,
                email=email
            )
        if voyageur_id:
            Voyageur.objects.filter(id=voyageur_id).update(
                guest_id=guest_id,
                email=email
            )

        # Mettre à jour la session avec le nouveau guest_id propre
        request.session['guest_id'] = guest_id
        request.session['profil_id'] = profil.id

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def creer_profil_page(request):
    expediteur_id = request.GET.get('expediteur_id', '')
    nom_complet = ''

    if expediteur_id:
        try:
            exp = Expediteur.objects.get(id=expediteur_id)
            nom_complet = f"{exp.prenom} {exp.nom}"
            # ✅ CORRECTION : on synchronise le guest_id de session UNIQUEMENT
            # si on vient de créer cet expéditeur dans la même session
            # (i.e. le guest_id de session correspond déjà à cet expéditeur)
            # On NE remplace plus la session par le guest_id de l'expéditeur
            # car cela causerait l'héritage de ses données pour tout nouveau visiteur
            session_guest_id = request.session.get('guest_id')
            if exp.guest_id and exp.guest_id == session_guest_id:
                # Même session → OK, c'est bien l'auteur de cette annonce
                pass
            # Sinon : ne rien faire sur la session — laisser chaque visiteur isolé
        except Expediteur.DoesNotExist:
            pass

    return render(request, 'voyageurs/creer_profil_page.html', {
        'expediteur_id': expediteur_id,
        'nom_complet': nom_complet,
        'type_profil': 'expediteur',
    })


def login_profil(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'})
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    try:
        profil = Profil.objects.get(username=username, password=password)
        request.session['guest_id'] = profil.guest_id
        request.session['profil_id'] = profil.id
        return JsonResponse({
            'status': 'ok',
            'type_profil': profil.type_profil,
            'nom_complet': profil.nom_complet,
            'telephone': profil.telephone,
            'guest_id': profil.guest_id,
            'profil_id': profil.id
        })
    except Profil.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Identifiants incorrects'})


def page_login(request):
    return render(request, 'voyageurs/login.html')


def google_callback(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('/')
    try:
        social_account = user.socialaccount_set.filter(provider='google').first()
        extra_data = social_account.extra_data if social_account else {}
    except Exception:
        extra_data = {}

    google_name = extra_data.get('name', user.get_full_name() or user.username or 'Utilisateur')
    google_email = extra_data.get('email', user.email or '')

    profil_existant = Profil.objects.filter(email=google_email).first()
    if profil_existant:
        request.session['profil_id'] = profil_existant.id
        request.session['guest_id'] = profil_existant.guest_id
        return redirect('/espace-connecte/')
    else:
        request.session['google_name'] = google_name
        request.session['google_email'] = google_email
        nouveau_guest_id = str(uuid.uuid4())
        request.session['guest_id'] = nouveau_guest_id
        request.session['profil_id'] = None
        return redirect('/completer-profil-google/')


def completer_profil_google(request):
    return render(request, 'voyageurs/completer_profil_google.html', {
        'google_name': request.session.get('google_name', ''),
        'google_email': request.session.get('google_email', ''),
    })


def page_paiement(request):
    expediteur_id = request.GET.get('expediteur_id')
    mode_paiement = request.GET.get('mode_paiement', 'carte')
    montant = request.GET.get('montant', '0')
    return render(request, 'voyageurs/paiement.html', {
        'expediteur_id': expediteur_id,
        'mode_paiement': mode_paiement,
        'montant': montant,
    })


@require_POST
def traiter_paiement(request):
    try:
        expediteur_id = request.POST.get('expediteur_id')
        mode_paiement = request.POST.get('mode_paiement')
        montant = float(request.POST.get('montant', 0))

        expediteur = Expediteur.objects.get(id=expediteur_id)
        reference = 'KRL-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        expediteur.paiement_effectue = True
        expediteur.reference_paiement = reference
        expediteur.date_paiement = timezone.now()
        expediteur.save()

        matching = expediteur.matchings.first()
        voyageur = matching.voyageur if matching else None

        montant_voyageur = expediteur.poids_colis * 10
        montant_commission = expediteur.poids_colis * 0.20

        Transaction.objects.create(
            expediteur=expediteur,
            voyageur=voyageur,
            montant=montant,
            montant_voyageur=montant_voyageur,
            montant_commission=montant_commission,
            mode_paiement=mode_paiement,
            statut='bloque'
        )

        profil_id_session = request.session.get('profil_id')
        has_profil = bool(profil_id_session and Profil.objects.filter(id=profil_id_session).exists())

        # ✅ Données pour la facture PDF/HTML côté client
        return JsonResponse({
            'status': 'ok',
            'reference': reference,
            'has_matching': matching is not None,
            'has_profil': has_profil,
            'message': f'Paiement de {montant}€ sécurisé ✅',
            # Données facture
            'facture': {
                'reference': reference,
                'nom': f"{expediteur.prenom} {expediteur.nom}",
                'montant': montant,
                'montant_voyageur': montant_voyageur,
                'montant_commission': montant_commission,
                'mode_paiement': mode_paiement,
                'trajet': f"{expediteur.ville} → {expediteur.ville_destination}",
                'poids': expediteur.poids_colis,
                'date': timezone.now().strftime('%d/%m/%Y à %H:%M'),
                'expediteur_id': expediteur.id,
            }
        })
    except Expediteur.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Expéditeur introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def espace_connecte(request):

    profil_id = request.session.get('profil_id')
    if not profil_id:
        return render(request, 'voyageurs/login.html')

    profil = Profil.objects.filter(id=profil_id).first()
    if not profil:
        return render(request, 'voyageurs/login.html')

    type_profil  = profil.type_profil
    nom_complet  = profil.nom_complet
    nom_initiale = nom_complet[0].upper() if nom_complet else '?'
    # ✅ ISOLATION : toujours depuis la DB, jamais la session directe
    guest_id = profil.guest_id

    # ================================================================
    # ✅ MATCHINGS — filtrés strictement par guest_id du profil connecté
    # ================================================================
    if type_profil == 'expediteur':
        matchings = Matching.objects.filter(
            expediteur__guest_id=guest_id
        ).select_related('expediteur', 'voyageur').order_by('-date_creation')
    else:
        matchings = Matching.objects.filter(
            voyageur__guest_id=guest_id
        ).select_related('expediteur', 'voyageur').order_by('-date_creation')

    matchings_confirmes = matchings.filter(
        statut__in=['en_attente', 'accepte', 'livre']
    ).count()

    matchings_livres = matchings.filter(
        livraison_confirmee_voyageur=True
    ) if type_profil == 'expediteur' else matchings.filter(statut='livre')

# ================================================================
    # ✅ DONNÉES EXPÉDITEUR
    # ================================================================
    if type_profil == 'expediteur':
        matchings_avec_chat = matchings.filter(
            statut__in=['accepte', 'livre'],
            expediteur__paiement_effectue=True
        )
        transactions_remboursables = Transaction.objects.filter(
            expediteur__guest_id=guest_id,
            statut='bloque'
        ).select_related('expediteur').order_by('-date_transaction')

        transactions_payees = Transaction.objects.filter(
            expediteur__guest_id=guest_id,
            statut__in=['bloque', 'debloque', 'rembourse', 'remboursement_demande']
        ).select_related('expediteur').order_by('-date_transaction')

        transactions_debloquees = []
        retraits_effectues = []
        portefeuille = None
        solde_actuel = 0.0
        demandes_en_attente = []

    # ================================================================
    # ✅ DONNÉES VOYAGEUR
    # ================================================================
    else:
        matchings_avec_chat = matchings.filter(statut__in=['accepte', 'livre'])
        transactions_remboursables = []
        transactions_payees = []
        demandes_en_attente = matchings.filter(statut='en_attente')

        portefeuille, _ = Portefeuille.objects.get_or_create(
            guest_id=guest_id,
            defaults={'nom_complet': nom_complet, 'solde': 0.0}
        )
        solde_actuel = float(portefeuille.solde)

        retraits_effectues = Retrait.objects.filter(
            guest_id=guest_id
        ).order_by('-date_demande')[:10]

        t_par_voyageur = Transaction.objects.filter(
            voyageur__guest_id=guest_id,
            statut='debloque'
        ).select_related('expediteur', 'voyageur').order_by('-date_transaction')

        expediteur_ids_de_ce_voyageur = Matching.objects.filter(
            voyageur__guest_id=guest_id
        ).values_list('expediteur_id', flat=True)

        t_par_matching = Transaction.objects.filter(
            expediteur_id__in=expediteur_ids_de_ce_voyageur,
            statut='debloque',
            voyageur__isnull=True
        ).select_related('expediteur').order_by('-date_transaction')

        ids_deja = set(t_par_voyageur.values_list('id', flat=True))
        extra = [t for t in t_par_matching if t.id not in ids_deja]

        from itertools import chain
        transactions_debloquees = sorted(
            list(chain(t_par_voyageur, extra)),
            key=lambda t: t.date_transaction,
            reverse=True
        )

    # ================================================================
    # ✅ SUPPORT
    # ================================================================
    messages_support = MessageSupport.objects.filter(
        guest_id=guest_id
    ).order_by('date')

    nb_support_non_lus = MessageSupport.objects.filter(
        guest_id=guest_id, sender='admin', lu=False
    ).count()

    return render(request, 'voyageurs/espace_connecte.html', {
        'type_profil':                type_profil,
        'nom_complet':                nom_complet,
        'nom_initiale':               nom_initiale,
        'matchings':                  matchings,
        'matchings_confirmes':        matchings_confirmes,
        'matchings_avec_chat':        matchings_avec_chat,
        'matchings_livres':           matchings_livres,
        'demandes_en_attente':        demandes_en_attente,
        'transactions_remboursables': transactions_remboursables,
        'transactions_payees':        transactions_payees,
        'transactions_debloquees':    transactions_debloquees,
        'retraits_effectues':         retraits_effectues,
        'messages_support':           messages_support,
        'nb_support_non_lus':         nb_support_non_lus,
        'guest_id':                   guest_id,
        'portefeuille':               portefeuille,
        'solde_actuel':               solde_actuel,
    })


def _diminuer_poids_voyageur_si_detail(voyageur, poids_colis):
    if voyageur.type_kg == 'detail':
        voyageur.poids_disponible = max(0, voyageur.poids_disponible - poids_colis)
        if voyageur.poids_disponible <= 0:
            voyageur.poids_disponible = 0
            voyageur.statut = 'complet'
            voyageur.is_matched = True
        voyageur.save()
    else:
        voyageur.poids_disponible = 0
        voyageur.statut = 'complet'
        voyageur.is_matched = True
        voyageur.save()


@require_POST
def repondre_matching(request):
    """
    Le VOYAGEUR répond à une demande.
    Email → EXPÉDITEUR dans les deux cas (acceptation ou refus).
    """
    try:
        matching_id = request.POST.get('matching_id')
        decision = request.POST.get('decision')
        profil_id = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        profil = Profil.objects.filter(id=profil_id).first()
        guest_id = profil.guest_id if profil else None

        matching = Matching.objects.get(id=matching_id, voyageur__guest_id=guest_id)

        if decision not in ['accepte', 'refuse']:
            return JsonResponse({'status': 'error', 'message': 'Décision invalide'})

        matching.statut = decision
        matching.save()

        nom_exp = f"{matching.expediteur.prenom} {matching.expediteur.nom}"
        nom_voy = f"{matching.voyageur.prenom} {matching.voyageur.nom}"
        ville_dep = matching.expediteur.ville
        ville_dest = matching.expediteur.ville_destination

        email_exp = _get_email_expediteur(matching.expediteur)
        print(f"[REPONDRE_MATCHING] decision={decision}, email_exp={email_exp}")

        if decision == 'accepte':
            matching.expediteur.is_matched = True
            matching.expediteur.save()
            if email_exp:
                email_acceptation_expediteur(email_exp, nom_exp, nom_voy, ville_dep, ville_dest)
        else:
            if email_exp:
                email_refus_expediteur(email_exp, nom_exp, nom_voy, ville_dep, ville_dest)

        return JsonResponse({'status': 'ok'})

    except Matching.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Matching introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def envoyer_message(request):
    """
    Envoie un message dans le chat.
    ✅ Notifications email de message reçu SUPPRIMÉES.
    """
    try:
        matching_id = request.POST.get('matching_id')
        contenu = request.POST.get('contenu', '').strip()
        profil_id = request.session.get('profil_id')

        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        profil = Profil.objects.filter(id=profil_id).first()
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Profil introuvable'})

        guest_id = profil.guest_id
        matching = Matching.objects.get(id=matching_id)

        is_expediteur = (matching.expediteur.guest_id == guest_id)
        is_voyageur = (matching.voyageur.guest_id == guest_id)

        if not is_expediteur and not is_voyageur:
            return JsonResponse({'status': 'error', 'message': 'Accès refusé'})

        sender = 'expediteur' if is_expediteur else 'voyageur'

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

        # ✅ Aucun email envoyé pour les messages — fonctionnalité désactivée

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
        print(f"[ERREUR envoyer_message] {e}")
        return JsonResponse({'status': 'error', 'message': str(e)})


def get_messages(request):
    """
    Retourne les messages avec is_mine correctement calculé.
    is_mine = True si sender == mon_role (rôle de l'utilisateur connecté).
    """
    try:
        matching_id = request.GET.get('matching_id')
        since_id = int(request.GET.get('since_id', 0))
        profil_id = request.session.get('profil_id')

        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        profil = Profil.objects.filter(id=profil_id).first()
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Profil introuvable'})

        guest_id = profil.guest_id
        matching = Matching.objects.get(id=matching_id)

        is_expediteur = (matching.expediteur.guest_id == guest_id)
        is_voyageur = (matching.voyageur.guest_id == guest_id)

        if not is_expediteur and not is_voyageur:
            return JsonResponse({'status': 'error', 'message': 'Accès refusé'})

        mon_role = 'expediteur' if is_expediteur else 'voyageur'

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
        profil_id = request.session.get('profil_id')
        guest_id = request.session.get('guest_id', '')
        nom_complet = 'Utilisateur'
        type_profil = 'inconnu'

        if profil_id:
            profil = Profil.objects.filter(id=profil_id).first()
            if profil:
                guest_id = profil.guest_id
                nom_complet = profil.nom_complet
                type_profil = profil.type_profil

        msg = MessageSupport.objects.create(
            guest_id=guest_id, nom_complet=nom_complet,
            type_profil=type_profil, sender='user', contenu=contenu
        )
        return JsonResponse({'status': 'ok', 'message_id': msg.id,
                             'contenu': contenu, 'date': msg.date.strftime('%H:%M')})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def get_messages_support(request):
    try:
        profil_id = request.session.get('profil_id')
        since_id = int(request.GET.get('since_id', 0))
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        profil = Profil.objects.filter(id=profil_id).first()
        # ✅ ISOLATION : messages support par guest_id du profil connecté
        guest_id = profil.guest_id

        messages = MessageSupport.objects.filter(
            guest_id=guest_id, id__gt=since_id
        ).order_by('date')
        MessageSupport.objects.filter(
            guest_id=guest_id, sender='admin', lu=False
        ).update(lu=True)

        data = [{'id': m.id, 'sender': m.sender, 'contenu': m.contenu,
                 'date': m.date.strftime('%H:%M'), 'is_mine': m.sender == 'user'} for m in messages]
        return JsonResponse({'status': 'ok', 'messages': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ================================================================
# VUE Django — remplacez confirmer_livraison_voyageur dans views.py
# Gère photo_base64 (caméra) ET photo fichier (fallback)
# ================================================================

@require_POST
def confirmer_livraison_voyageur(request):
    try:
        profil_id = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        profil = Profil.objects.filter(id=profil_id).first()
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Profil introuvable'})

        matching_id = request.POST.get('matching_id')
        photo_base64 = request.POST.get('photo_base64', '').strip()
        photo_fichier = request.FILES.get('photo')

        # ✅ Vérifier qu'on a bien une photo (base64 OU fichier)
        if not photo_base64 and not photo_fichier:
            return JsonResponse({'status': 'error', 'message': 'La photo est obligatoire'})

        matching = Matching.objects.get(id=matching_id, voyageur__guest_id=profil.guest_id)

        # ✅ Conversion base64 → fichier image
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
                return JsonResponse({'status': 'error', 'message': 'Format de photo invalide : ' + str(e)})
        else:
            # Fichier uploadé directement (fallback)
            photo_file = photo_fichier

        # Mise à jour du matching
        matching.livraison_confirmee_voyageur = True
        matching.date_livraison = timezone.now()
        matching.statut = 'livre'
        matching.photo_livraison = photo_file
        matching.save()

        # Message avec photo dans le chat
        Message.objects.create(
            expediteur=matching.expediteur,
            voyageur=matching.voyageur,
            sender='voyageur',
            contenu='📦 Photo de confirmation de livraison',
            photo=photo_file,
            est_photo_livraison=True
        )

        # Email à l'expéditeur
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
            'message': 'Livraison confirmée ✅. Photo envoyée à l\'expéditeur.'
        })

    except Matching.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Matching introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@require_POST
def confirmer_reception_expediteur(request):
    """
    L'EXPÉDITEUR confirme la réception → gains débloqués au VOYAGEUR.
    Email au VOYAGEUR.
    """
    try:
        profil_id = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        profil = Profil.objects.filter(id=profil_id).first()
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Profil introuvable'})

        matching_id = request.POST.get('matching_id')
        matching = Matching.objects.get(id=matching_id, expediteur__guest_id=profil.guest_id)

        matching.expediteur.livraison_confirmee_expediteur = True
        matching.expediteur.date_confirmation_expediteur = timezone.now()
        matching.expediteur.save()

        transaction = Transaction.objects.filter(
            expediteur=matching.expediteur, statut='bloque'
        ).first()

        nom_expediteur = f"{matching.expediteur.prenom} {matching.expediteur.nom}"

        if transaction:
            transaction.statut = 'debloque'
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

                # ✅ Email au VOYAGEUR : gains débloqués
                email_voy = _get_email_voyageur(voyageur)
                print(f"[RECEPTION] email_voy={email_voy}")
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


def debloquer_paiement_admin(request, transaction_id):
    """Admin débloque manuellement → gains crédités au voyageur."""
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
        transaction_id = request.POST.get('transaction_id')
        transaction = Transaction.objects.get(id=transaction_id)
        transaction.statut = 'debloque'
        transaction.save()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@require_POST
def demander_remboursement(request):
    try:
        profil_id = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        profil = Profil.objects.filter(id=profil_id).first()
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Profil introuvable'})

        transaction_id = request.POST.get('transaction_id')
        
        # ✅ ISOLATION : vérifier que la transaction appartient bien à cet expéditeur
        transaction = Transaction.objects.get(
            id=transaction_id,
            expediteur__guest_id=profil.guest_id,
            statut='bloque'
        )

        transaction.statut = 'remboursement_demande'
        transaction.note_remboursement = request.POST.get('motif', 'Aucun voyageur trouvé')
        transaction.save()

        # ✅ Données pour la facture
        facture_data = {
            'reference': transaction.expediteur.reference_paiement or f"KRL-RMB-{transaction.id}",
            'nom': f"{transaction.expediteur.prenom} {transaction.expediteur.nom}",
            'montant_paye': float(transaction.montant),
            'montant_rembourse': float(transaction.montant_voyageur),
            'montant_commission': float(transaction.montant_commission),
            'trajet': f"{transaction.expediteur.ville} → {transaction.expediteur.ville_destination}",
            'poids': float(transaction.expediteur.poids_colis),
            'date': timezone.now().strftime('%d/%m/%Y à %H:%M'),
        }

        # URL de la facture (on va créer cette vue juste après)
        facture_url = reverse('generer_facture_remboursement', kwargs={'transaction_id': transaction.id})

        return JsonResponse({
            'status': 'ok',
            'message': 'Demande envoyée ✅. Traitement sous 48h.',
            'facture_url': facture_url,
            'facture': facture_data
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
        profil_id = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        profil = Profil.objects.filter(id=profil_id).first()
        portefeuille, _ = Portefeuille.objects.get_or_create(
            guest_id=profil.guest_id,
            defaults={'nom_complet': profil.nom_complet}
        )
        retraits = Retrait.objects.filter(
            guest_id=profil.guest_id
        ).order_by('-date_demande')[:10]
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


def _retrait_auto_si_coordonnees(guest_id_voyageur, montant, nom_voyageur):
    try:
        dernier = Retrait.objects.filter(
            guest_id=guest_id_voyageur,
            coordonnees__isnull=False
        ).exclude(coordonnees='').order_by('-date_demande').first()

        if dernier:
            portefeuille = Portefeuille.objects.filter(guest_id=guest_id_voyageur).first()
            if portefeuille and portefeuille.solde >= montant:
                Retrait.objects.create(
                    guest_id=guest_id_voyageur,
                    nom_complet=nom_voyageur,
                    montant=montant,
                    mode_retrait=dernier.mode_retrait,
                    coordonnees=dernier.coordonnees,
                    statut='traite'
                )
                portefeuille.solde -= montant
                portefeuille.save()
    except Exception:
        pass


@require_POST
def demander_retrait(request):
    try:
        profil_id = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        profil = Profil.objects.filter(id=profil_id).first()

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
        matching_id = request.GET.get('matching_id')
        matching = Matching.objects.get(id=matching_id)
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


def get_expediteur_info(request):
    try:
        expediteur_id = request.GET.get('expediteur_id')
        exp = Expediteur.objects.get(id=expediteur_id)
        return JsonResponse({
            'status': 'ok',
            'pays_depart': exp.pays,
            'ville_depart': exp.ville,
            'pays_destination': exp.pays_destination,
            'ville_destination': exp.ville_destination,
            'poids': exp.poids_colis,
        })
    except Expediteur.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Expéditeur introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def get_voyageur_info(request):
    try:
        voyageur_id = request.GET.get('voyageur_id')
        v = Voyageur.objects.get(id=voyageur_id)
        return JsonResponse({
            'status': 'ok',
            'poids_disponible': v.poids_disponible,
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


@require_POST
def creer_matching_apres_login(request):
    try:
        profil_id = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})

        profil = Profil.objects.filter(id=profil_id).first()
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Profil introuvable'})

        type_match = request.POST.get('type')
        guest_id = profil.guest_id

        if type_match == 'voyageur':
            expediteur_id = request.POST.get('expediteur_id')
            expediteur = Expediteur.objects.get(id=expediteur_id)

            voyageur = Voyageur.objects.filter(guest_id=guest_id).last()
            if not voyageur:
                return JsonResponse({'status': 'need_form', 'message': 'Remplir le formulaire'})

            # 🔥 ISOLATION FIX
            expediteur.guest_id = guest_id
            expediteur.save()

            voyageur.guest_id = voyageur.guest_id or guest_id
            voyageur.save()

            Matching.objects.get_or_create(
                expediteur=expediteur,
                voyageur=voyageur,
                defaults={'statut': 'en_attente'}
            )

            expediteur.is_matched = True
            expediteur.save()

            return JsonResponse({'status': 'ok', 'redirect': '/espace-connecte/'})

        elif type_match == 'expediteur':
            voyageur_id = request.POST.get('voyageur_id')
            voyageur = Voyageur.objects.get(id=voyageur_id)

            expediteur = Expediteur.objects.filter(guest_id=guest_id).last()
            if not expediteur:
                return JsonResponse({'status': 'need_form', 'message': 'Remplir le formulaire'})

            # 🔥 ISOLATION FIX
            expediteur.guest_id = expediteur.guest_id or guest_id
            expediteur.save()

            voyageur.guest_id = guest_id
            voyageur.save()

            Matching.objects.get_or_create(
                expediteur=expediteur,
                voyageur=voyageur,
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
    return JsonResponse({'status': 'ok'})


@require_POST
def refuser_demande(request):
    return JsonResponse({'status': 'ok'})


def get_solde_temps_reel(request):
    profil_id = request.session.get('profil_id')
    if not profil_id:
        return JsonResponse({'status': 'error', 'message': 'Non connecté'})
    profil = Profil.objects.filter(id=profil_id).first()
    if not profil:
        return JsonResponse({'status': 'error', 'message': 'Introuvable'})
    portefeuille = Portefeuille.objects.filter(guest_id=profil.guest_id).first()
    solde = portefeuille.solde if portefeuille else 0.0
    return JsonResponse({'status': 'ok', 'solde': solde})


def _get_nom_profil(guest_id):
    profil = Profil.objects.filter(guest_id=guest_id).first()
    return profil.nom_complet if profil else 'Utilisateur'

def generer_facture_remboursement(request, transaction_id):
    try:
        transaction = get_object_or_404(Transaction, id=transaction_id)
        
        # On utilise la référence originale du paiement
        reference = transaction.expediteur.reference_paiement or f"KRL-PAI-{transaction.id}"

        context = {
            'reference': reference,
            'nom': f"{transaction.expediteur.prenom} {transaction.expediteur.nom}",
            'montant_paye': float(transaction.montant),
            'montant_rembourse': float(transaction.montant_voyageur),
            'montant_commission': float(transaction.montant_commission),
            'trajet': f"{transaction.expediteur.ville} → {transaction.expediteur.ville_destination}",
            'poids': float(transaction.expediteur.poids_colis),
            'date': timezone.now().strftime('%d/%m/%Y à %H:%M'),
        }
        
        html_content = render_to_string('voyageurs/facture_remboursement.html', context)
        
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="Facture_Remboursement_{reference}.html"'
        
        return response
        
    except Exception as e:
        return HttpResponse(f"Erreur lors de la génération de la facture : {str(e)}", status=500)    