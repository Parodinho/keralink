from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import uuid, random, string
from django.http import HttpResponse
import base64
from django.utils import translation
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
    email_livraison_confirmee_expediteur,
    email_gains_debloques_voyageur,
    email_confirmation_reception_voyageur,
)

# ✅ Commission fixe KERALINK
COMMISSION_KERALINK = 2.99


# ================================================================
# HELPERS EMAIL
# ================================================================

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


def _get_email_profil(guest_id):
    if not guest_id:
        return None
    profil = Profil.objects.filter(guest_id=guest_id).first()
    if profil and profil.email and '@' in str(profil.email):
        return profil.email
    return None


# ================================================================
# HOME
# ================================================================

def home(request):
    if not request.session.get('guest_id'):
        request.session['guest_id'] = str(uuid.uuid4())

    guest_id = request.session['guest_id']

    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
         or request.META.get('REMOTE_ADDR', '')

    visiteur, cree = Visiteur.objects.get_or_create(
        guest_id=guest_id,
        defaults={'ip_address': ip or None}
    )
    if not cree:
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


def nb_visiteurs(request):
    total = Visiteur.objects.count()
    return JsonResponse({'status': 'ok', 'total': total})


def historique(request):
    profil_id = request.session.get('profil_id')
    transactions = []
    if profil_id:
        profil = Profil.objects.filter(id=profil_id).first()
        if profil:
            transactions = Transaction.objects.filter(
                expediteur__guest_id=profil.guest_id
            ).order_by('-date_transaction')
    return render(request, 'voyageurs/historique.html', {'transactions': transactions})


# ================================================================
# ✅ AJOUTER EXPÉDITEUR — nouveau calcul prix libre + commission 2.99
# ================================================================

@require_POST
def ajouter_expediteur(request):
    try:
        mode  = request.POST.get('mode', 'normal')
        poids = float(request.POST.get('poids'))
        # ✅ prix_par_kg saisi par l'expéditeur (ou hérité du voyageur)
        prix_par_kg  = float(request.POST.get('prix_par_kg', 10.0))
        # prix_total = ce que le voyageur reçoit (sans commission)
        prix_total   = round(poids * prix_par_kg, 2)
        # montant total payé = prix_total + commission fixe 2.99€
        montant_total = round(prix_total + COMMISSION_KERALINK, 2)

        if mode == 'normal':
            nouveau_guest_id = str(uuid.uuid4())
            request.session['guest_id']  = nouveau_guest_id
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
                guest_id = profil_connecte.guest_id

        expediteur = Expediteur.objects.create(
            nom=request.POST.get('nom'),
            prenom=request.POST.get('prenom'),
            telephone=request.POST.get('telephone'),
            pays=request.POST.get('pays'),
            ville=request.POST.get('ville'),
            pays_destination=request.POST.get('pays_destination'),
            ville_destination=request.POST.get('ville_destination'),
            poids_colis=poids,
            prix_par_kg=prix_par_kg,
            prix_total=prix_total,
            commission=COMMISSION_KERALINK,
            mode_paiement=request.POST.get('mode_paiement'),
            guest_id=guest_id,
            is_matched=False,
            is_created_via_matching=(mode == 'matching'),
            paiement_effectue=False,
            email=email_exp_connecte,
        )

        if mode == 'matching':
            voyageur_id = request.POST.get('voyageur_id')
            voyageur    = Voyageur.objects.get(id=voyageur_id)
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

        return JsonResponse({
            'status':        'ok',
            'expediteur_id': expediteur.id,
            'montant_total': montant_total,
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ================================================================
# ✅ AJOUTER VOYAGEUR — prix_par_kg libre
# ================================================================

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
                guest_id = profil_connecte.guest_id

        # ✅ prix_par_kg saisi par le voyageur
        prix_par_kg = float(request.POST.get('prix_par_kg', 10.0))

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
            prix_par_kg=prix_par_kg,
            type_kg=request.POST.get('type_kg', 'entier'),
            guest_id=guest_id,
            is_matched=False,
            is_created_via_matching=(mode == 'matching'),
            email=email_voy_connecte,
        )

        if mode == 'matching':
            expediteur_id = request.POST.get('expediteur_id')
            expediteur    = Expediteur.objects.get(id=expediteur_id)
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


# ================================================================
# ✅ TRAITER PAIEMENT — nouveau calcul
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

        # ✅ montant_voyageur = prix_total (poids × prix_par_kg) — sans commission
        montant_voyageur   = expediteur.prix_total
        # ✅ commission fixe 2.99€
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

        profil_id_session = request.session.get('profil_id')
        has_profil = bool(
            profil_id_session and Profil.objects.filter(id=profil_id_session).exists()
        )

        return JsonResponse({
            'status':       'ok',
            'reference':    reference,
            'has_matching': matching is not None,
            'has_profil':   has_profil,
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


# ================================================================
# GET VOYAGEUR INFO — inclut prix_par_kg
# ================================================================

def get_voyageur_info(request):
    try:
        voyageur_id = request.GET.get('voyageur_id')
        v = Voyageur.objects.get(id=voyageur_id)
        return JsonResponse({
            'status':            'ok',
            'poids_disponible':  v.poids_disponible,
            'prix_par_kg':       v.prix_par_kg,
            'ville_depart':      v.ville_depart,
            'pays_depart':       v.pays_depart,
            'ville_destination': v.ville_destination,
            'pays_destination':  v.pays_destination,
            'type_kg':           v.type_kg,
        })
    except Voyageur.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Voyageur introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def get_expediteur_info(request):
    try:
        expediteur_id = request.GET.get('expediteur_id')
        exp = Expediteur.objects.get(id=expediteur_id)
        return JsonResponse({
            'status':            'ok',
            'pays_depart':       exp.pays,
            'ville_depart':      exp.ville,
            'pays_destination':  exp.pays_destination,
            'ville_destination': exp.ville_destination,
            'poids':             exp.poids_colis,
            'prix_par_kg':       exp.prix_par_kg,
        })
    except Expediteur.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Expéditeur introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ================================================================
# CONFIRMER RÉCEPTION — gains = montant_voyageur (prix_total)
# ================================================================

@require_POST
def confirmer_reception_expediteur(request):
    try:
        profil_id = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        profil = Profil.objects.filter(id=profil_id).first()
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Profil introuvable'})

        matching_id = request.POST.get('matching_id')
        matching    = Matching.objects.get(id=matching_id, expediteur__guest_id=profil.guest_id)

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
                # ✅ Voyageur reçoit montant_voyageur (= prix_total sans commission)
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
            'status':  'ok',
            'message': 'Réception confirmée ✅ Gains débloqués vers le voyageur.'
        })
    except Matching.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Matching introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ================================================================
# TOUTES LES AUTRES VUES (inchangées)
# ================================================================

@require_POST
def creer_profil(request):
    try:
        username = request.POST.get('username', '').strip()
        if Profil.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Nom utilisateur déjà utilisé'})

        email         = request.POST.get('email', '')
        expediteur_id = request.POST.get('expediteur_id')
        voyageur_id   = request.POST.get('voyageur_id')

        if expediteur_id:
            try:
                exp      = Expediteur.objects.get(id=expediteur_id)
                guest_id = exp.guest_id if exp.guest_id else str(uuid.uuid4())
            except Expediteur.DoesNotExist:
                guest_id = str(uuid.uuid4())
        elif voyageur_id:
            try:
                voy      = Voyageur.objects.get(id=voyageur_id)
                guest_id = voy.guest_id if voy.guest_id else str(uuid.uuid4())
            except Voyageur.DoesNotExist:
                guest_id = str(uuid.uuid4())
        else:
            guest_id = str(uuid.uuid4())

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

        if expediteur_id:
            Expediteur.objects.filter(id=expediteur_id).update(guest_id=guest_id, email=email)
        if voyageur_id:
            Voyageur.objects.filter(id=voyageur_id).update(guest_id=guest_id, email=email)

        request.session['guest_id']  = guest_id
        request.session['profil_id'] = profil.id
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def creer_profil_page(request):
    expediteur_id = request.GET.get('expediteur_id', '')
    nom_complet = ''
    if expediteur_id:
        try:
            exp         = Expediteur.objects.get(id=expediteur_id)
            nom_complet = f"{exp.prenom} {exp.nom}"
        except Expediteur.DoesNotExist:
            pass
    return render(request, 'voyageurs/creer_profil_page.html', {
        'expediteur_id': expediteur_id,
        'nom_complet':   nom_complet,
        'type_profil':   'expediteur',
    })


def login_profil(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'})
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    try:
        profil = Profil.objects.get(username=username, password=password)
        request.session['guest_id']  = profil.guest_id
        request.session['profil_id'] = profil.id
        return JsonResponse({
            'status':      'ok',
            'type_profil': profil.type_profil,
            'nom_complet': profil.nom_complet,
            'telephone':   profil.telephone,
            'guest_id':    profil.guest_id,
            'profil_id':   profil.id
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
        extra_data     = social_account.extra_data if social_account else {}
    except Exception:
        extra_data = {}

    google_name  = extra_data.get('name', user.get_full_name() or user.username or 'Utilisateur')
    google_email = extra_data.get('email', user.email or '')

    profil_existant = Profil.objects.filter(email=google_email).first()
    if profil_existant:
        request.session['profil_id'] = profil_existant.id
        request.session['guest_id']  = profil_existant.guest_id
        return redirect('/espace-connecte/')
    else:
        request.session['google_name']  = google_name
        request.session['google_email'] = google_email
        nouveau_guest_id = str(uuid.uuid4())
        request.session['guest_id']  = nouveau_guest_id
        request.session['profil_id'] = None
        return redirect('/completer-profil-google/')


def completer_profil_google(request):
    return render(request, 'voyageurs/completer_profil_google.html', {
        'google_name':  request.session.get('google_name', ''),
        'google_email': request.session.get('google_email', ''),
    })


def page_paiement(request):
    expediteur_id = request.GET.get('expediteur_id')
    mode_paiement = request.GET.get('mode_paiement', 'carte')
    montant       = request.GET.get('montant', '0')
    return render(request, 'voyageurs/paiement.html', {
        'expediteur_id': expediteur_id,
        'mode_paiement': mode_paiement,
        'montant':       montant,
    })


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
    guest_id     = profil.guest_id

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

    matchings_livres = (
        matchings.filter(livraison_confirmee_voyageur=True)
        if type_profil == 'expediteur'
        else matchings.filter(statut='livre')
    )

    if type_profil == 'expediteur':
        matchings_avec_chat = matchings.filter(
            statut__in=['accepte', 'livre'],
            expediteur__paiement_effectue=True
        )
        transactions_remboursables = Transaction.objects.filter(
            expediteur__guest_id=guest_id, statut='bloque'
        ).select_related('expediteur').order_by('-date_transaction')
        transactions_payees = Transaction.objects.filter(
            expediteur__guest_id=guest_id,
            statut__in=['bloque', 'debloque', 'rembourse', 'remboursement_demande']
        ).select_related('expediteur').order_by('-date_transaction')
        transactions_debloquees = []
        retraits_effectues      = []
        portefeuille            = None
        solde_actuel            = 0.0
        demandes_en_attente     = []
    else:
        matchings_avec_chat        = matchings.filter(statut__in=['accepte', 'livre'])
        transactions_remboursables = []
        transactions_payees        = []
        demandes_en_attente        = matchings.filter(statut='en_attente')

        portefeuille, _ = Portefeuille.objects.get_or_create(
            guest_id=guest_id,
            defaults={'nom_complet': nom_complet, 'solde': 0.0}
        )
        solde_actuel = float(portefeuille.solde)

        retraits_effectues = Retrait.objects.filter(
            guest_id=guest_id
        ).order_by('-date_demande')[:10]

        t_par_voyageur = Transaction.objects.filter(
            voyageur__guest_id=guest_id, statut='debloque'
        ).select_related('expediteur', 'voyageur').order_by('-date_transaction')

        expediteur_ids = Matching.objects.filter(
            voyageur__guest_id=guest_id
        ).values_list('expediteur_id', flat=True)

        t_par_matching = Transaction.objects.filter(
            expediteur_id__in=expediteur_ids,
            statut='debloque',
            voyageur__isnull=True
        ).select_related('expediteur').order_by('-date_transaction')

        ids_deja = set(t_par_voyageur.values_list('id', flat=True))
        extra    = [t for t in t_par_matching if t.id not in ids_deja]

        from itertools import chain
        transactions_debloquees = sorted(
            list(chain(t_par_voyageur, extra)),
            key=lambda t: t.date_transaction,
            reverse=True
        )

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
            voyageur.statut   = 'complet'
            voyageur.is_matched = True
        voyageur.save()
    else:
        voyageur.poids_disponible = 0
        voyageur.statut   = 'complet'
        voyageur.is_matched = True
        voyageur.save()


@require_POST
def repondre_matching(request):
    try:
        matching_id = request.POST.get('matching_id')
        decision    = request.POST.get('decision')
        profil_id   = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        profil   = Profil.objects.filter(id=profil_id).first()
        guest_id = profil.guest_id if profil else None
        matching = Matching.objects.get(id=matching_id, voyageur__guest_id=guest_id)
        if decision not in ['accepte', 'refuse']:
            return JsonResponse({'status': 'error', 'message': 'Décision invalide'})
        matching.statut = decision
        matching.save()
        nom_exp    = f"{matching.expediteur.prenom} {matching.expediteur.nom}"
        nom_voy    = f"{matching.voyageur.prenom} {matching.voyageur.nom}"
        ville_dep  = matching.expediteur.ville
        ville_dest = matching.expediteur.ville_destination
        email_exp  = _get_email_expediteur(matching.expediteur)
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
    try:
        matching_id = request.POST.get('matching_id')
        contenu     = request.POST.get('contenu', '').strip()
        profil_id   = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        profil = Profil.objects.filter(id=profil_id).first()
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Profil introuvable'})
        guest_id  = profil.guest_id
        matching  = Matching.objects.get(id=matching_id)
        is_exp    = (matching.expediteur.guest_id == guest_id)
        is_voy    = (matching.voyageur.guest_id   == guest_id)
        if not is_exp and not is_voy:
            return JsonResponse({'status': 'error', 'message': 'Accès refusé'})
        sender  = 'expediteur' if is_exp else 'voyageur'
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
            'status':              'ok',
            'message_id':          message.id,
            'date':                message.date.strftime('%H:%M'),
            'has_photo':           bool(message.photo),
            'photo_url':           message.photo.url if message.photo else None,
            'est_photo_livraison': message.est_photo_livraison,
            'sender':              sender,
        })
    except Matching.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Matching introuvable'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def get_messages(request):
    try:
        matching_id = request.GET.get('matching_id')
        since_id    = int(request.GET.get('since_id', 0))
        profil_id   = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        profil = Profil.objects.filter(id=profil_id).first()
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Profil introuvable'})
        guest_id = profil.guest_id
        matching = Matching.objects.get(id=matching_id)
        is_exp   = (matching.expediteur.guest_id == guest_id)
        is_voy   = (matching.voyageur.guest_id   == guest_id)
        if not is_exp and not is_voy:
            return JsonResponse({'status': 'error', 'message': 'Accès refusé'})
        mon_role = 'expediteur' if is_exp else 'voyageur'
        messages = Message.objects.filter(
            expediteur=matching.expediteur,
            voyageur=matching.voyageur,
            id__gt=since_id
        ).order_by('date')
        data = [{
            'id':                  m.id,
            'sender':              m.sender,
            'contenu':             m.contenu,
            'date':                m.date.strftime('%H:%M'),
            'is_mine':             (m.sender == mon_role),
            'has_photo':           bool(m.photo),
            'photo_url':           m.photo.url if m.photo else None,
            'est_photo_livraison': m.est_photo_livraison,
        } for m in messages]
        return JsonResponse({'status': 'ok', 'messages': data, 'mon_role': mon_role})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def envoyer_message_support(request):
    try:
        contenu     = request.POST.get('contenu', '').strip()
        if not contenu:
            return JsonResponse({'status': 'error', 'message': 'Message vide'})
        profil_id   = request.session.get('profil_id')
        guest_id    = request.session.get('guest_id', '')
        nom_complet = 'Utilisateur'
        type_profil = 'inconnu'
        if profil_id:
            profil = Profil.objects.filter(id=profil_id).first()
            if profil:
                guest_id    = profil.guest_id
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
        since_id  = int(request.GET.get('since_id', 0))
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        profil   = Profil.objects.filter(id=profil_id).first()
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


@require_POST
def confirmer_livraison_voyageur(request):
    try:
        profil_id = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        profil = Profil.objects.filter(id=profil_id).first()
        if not profil:
            return JsonResponse({'status': 'error', 'message': 'Profil introuvable'})

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
                    ext    = 'jpg'
                photo_data = base64.b64decode(imgstr)
                photo_file = ContentFile(photo_data, name=f'livraison_{matching.id}.{ext}')
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': 'Format photo invalide : ' + str(e)})
        else:
            photo_file = photo_fichier

        matching.livraison_confirmee_voyageur = True
        matching.date_livraison = timezone.now()
        matching.statut         = 'livre'
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
            'status':  'ok',
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
            transaction.statut       = 'debloque'
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
        transaction    = Transaction.objects.get(id=transaction_id)
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
        transaction = Transaction.objects.get(
            id=transaction_id,
            expediteur__guest_id=profil.guest_id,
            statut='bloque'
        )
        transaction.statut             = 'remboursement_demande'
        transaction.note_remboursement = request.POST.get('motif', 'Aucun voyageur trouvé')
        transaction.save()
        facture_url = reverse('generer_facture_remboursement', kwargs={'transaction_id': transaction.id})
        return JsonResponse({
            'status':      'ok',
            'message':     'Demande envoyée ✅. Traitement sous 48h.',
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
            'solde':  portefeuille.solde,
            'retraits': [{
                'montant':     r.montant,
                'mode':        r.mode_retrait,
                'coordonnees': r.coordonnees,
                'statut':      r.statut,
                'date':        r.date_demande.strftime('%d/%m/%Y à %H:%M')
            } for r in retraits]
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def demander_retrait(request):
    try:
        profil_id = request.session.get('profil_id')
        if not profil_id:
            return JsonResponse({'status': 'error', 'message': 'Non connecté'})
        profil      = Profil.objects.filter(id=profil_id).first()
        montant     = float(request.POST.get('montant', 0))
        mode        = request.POST.get('mode_retrait')
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
            'status':        'ok',
            'message':       f'Retrait de {montant:.2f}€ effectué ✅ — Envoi vers {coordonnees}',
            'nouveau_solde': portefeuille.solde
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def verifier_paiement(request):
    try:
        matching_id = request.GET.get('matching_id')
        matching    = Matching.objects.get(id=matching_id)
        nom      = f"{matching.expediteur.prenom} {matching.expediteur.nom}"
        initiale = matching.expediteur.prenom[0].upper() if matching.expediteur.prenom else '?'
        return JsonResponse({
            'status':              'ok',
            'paiement_effectue':   matching.expediteur.paiement_effectue,
            'expediteur_nom':      nom,
            'expediteur_initiale': initiale
        })
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
        guest_id   = profil.guest_id
        if type_match == 'voyageur':
            expediteur_id = request.POST.get('expediteur_id')
            expediteur    = Expediteur.objects.get(id=expediteur_id)
            voyageur      = Voyageur.objects.filter(guest_id=guest_id).last()
            if not voyageur:
                return JsonResponse({'status': 'need_form', 'message': 'Remplir le formulaire'})
            expediteur.guest_id = guest_id
            expediteur.save()
            Matching.objects.get_or_create(
                expediteur=expediteur, voyageur=voyageur,
                defaults={'statut': 'en_attente'}
            )
            expediteur.is_matched = True
            expediteur.save()
            return JsonResponse({'status': 'ok', 'redirect': '/espace-connecte/'})
        elif type_match == 'expediteur':
            voyageur_id = request.POST.get('voyageur_id')
            voyageur    = Voyageur.objects.get(id=voyageur_id)
            expediteur  = Expediteur.objects.filter(guest_id=guest_id).last()
            if not expediteur:
                return JsonResponse({'status': 'need_form', 'message': 'Remplir le formulaire'})
            voyageur.guest_id = guest_id
            voyageur.save()
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

def changer_langue(request):
    if request.method == 'POST':
        langue = request.POST.get('langue', 'fr')
        if langue in ['fr', 'en']:
            translation.activate(langue)
            request.session['_language'] = langue
            from django.http import JsonResponse
            response = JsonResponse({'status': 'ok', 'langue': langue})
            response.set_cookie('django_language', langue)
            return response
    from django.http import JsonResponse
    return JsonResponse({'status': 'error'})


def generer_facture_remboursement(request, transaction_id):
    try:
        transaction = get_object_or_404(Transaction, id=transaction_id)
        reference   = transaction.expediteur.reference_paiement or f"KRL-PAI-{transaction.id}"
        context = {
            'reference':          reference,
            'nom':                f"{transaction.expediteur.prenom} {transaction.expediteur.nom}",
            'montant_paye':       float(transaction.montant),
            'montant_rembourse':  float(transaction.montant_voyageur),
            'montant_commission': float(transaction.montant_commission),
            'trajet':             f"{transaction.expediteur.ville} → {transaction.expediteur.ville_destination}",
            'poids':              float(transaction.expediteur.poids_colis),
            'prix_par_kg':        float(transaction.expediteur.prix_par_kg),
            'date':               timezone.now().strftime('%d/%m/%Y à %H:%M'),
        }
        html_content = render_to_string('voyageurs/facture_remboursement.html', context)
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="Facture_Remboursement_{reference}.html"'
        return response
    except Exception as e:
        return HttpResponse(f"Erreur : {str(e)}", status=500)