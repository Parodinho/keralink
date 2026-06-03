from django.core.mail import send_mail
from django.conf import settings
import threading


def _envoyer_email_async(sujet, message_texte, destinataire):
    """Envoie l'email dans un thread séparé"""
    if not destinataire or '@' not in str(destinataire):
        print(f"[EMAIL ❌] Destinataire invalide : {destinataire}")
        return

    def _send():
        try:
            send_mail(
                subject=sujet,
                message=message_texte,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinataire],
                fail_silently=True,
                html_message=_wrap_html(sujet, message_texte),
            )
            print(f"[EMAIL ✅] Envoyé à {destinataire} | Sujet: {sujet}")
        except Exception as e:
            print(f"[EMAIL ❌] Erreur envoi à {destinataire} : {e}")

    t = threading.Thread(target=_send, daemon=True)
    t.start()


def _wrap_html(sujet, contenu_texte):
    """Template HTML KERALINK pour les emails."""
    lignes = contenu_texte.strip().split('\n')
    lignes_html = ''.join(
        f'<p style="margin:8px 0;color:#444;line-height:1.6;">{l.strip()}</p>'
        for l in lignes if l.strip()
    )
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f0f2f5;font-family:'Segoe UI',sans-serif;">
        <div style="max-width:580px;margin:30px auto;background:white;border-radius:14px;
                    overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
            <div style="background:linear-gradient(120deg,#0A1F44,#1E3A8A);
                        padding:28px 32px;text-align:center;">
                <h1 style="color:white;font-size:1.8rem;margin:0;letter-spacing:2px;">
                    KER<span style="color:#FF7A00;">ALINK</span>
                </h1>
                <p style="color:#a0cfff;font-size:0.85rem;margin:8px 0 0;">
                    Plateforme de transport de colis entre particuliers
                </p>
            </div>
            <div style="padding:32px;">
                <h2 style="color:#0A1F44;font-size:1.1rem;margin-bottom:20px;
                            padding-bottom:12px;border-bottom:3px solid #FF7A00;">
                    {sujet}
                </h2>
                <div style="background:#f9f9f9;border-radius:10px;padding:20px;">
                    {lignes_html}
                </div>
                <div style="margin-top:24px;text-align:center;">
                    <a href="http://localhost:8000/espace-connecte/"
                       style="background:linear-gradient(90deg,#FF7A00,#e66900);
                              color:white;padding:12px 28px;border-radius:10px;
                              text-decoration:none;font-weight:bold;font-size:0.95rem;
                              display:inline-block;">
                        → Accéder à mon espace KERALINK
                    </a>
                </div>
            </div>
            <div style="background:#f0f2f5;padding:16px 32px;text-align:center;
                        border-top:1px solid #e0e0e0;">
                <p style="color:#888;font-size:0.8rem;margin:0;">
                    © 2026 KERALINK — Cet email est automatique, merci de ne pas y répondre.<br>
                    Pour nous contacter, utilisez le support intégré à votre espace personnel.
                </p>
            </div>
        </div>
    </body>
    </html>
    """


# ================================================================
# ✅ FONCTIONS EMAIL — Matching & Notifications importantes
# ✅ Les notifications de message reçu ont été SUPPRIMÉES volontairement
# ================================================================

def email_matching_expediteur(email_exp, nom_exp, nom_voy, ville_dep, ville_dest, poids):
    """Email à l'expéditeur : un voyageur a matché avec son annonce."""
    _envoyer_email_async(
        sujet="🔗 Nouveau matching pour votre colis !",
        message_texte=f"""
Bonjour {nom_exp},

Un voyageur a sélectionné votre annonce.

Détails :
- Voyageur : {nom_voy}
- Trajet : {ville_dep} → {ville_dest}
- Poids : {poids} kg

Connectez-vous pour suivre votre demande.
        """,
        destinataire=email_exp
    )


def email_matching_voyageur(email_voy, nom_voy, nom_exp, ville_dep, ville_dest, poids):
    """Email au voyageur : un expéditeur a matché avec son annonce."""
    _envoyer_email_async(
        sujet="🔗 Nouvelle demande de matching sur votre trajet !",
        message_texte=f"""
Bonjour {nom_voy},

Un expéditeur souhaite vous confier un colis.

Détails :
- Expéditeur : {nom_exp}
- Trajet : {ville_dep} → {ville_dest}
- Poids : {poids} kg

Connectez-vous pour accepter ou refuser.
        """,
        destinataire=email_voy
    )


def email_acceptation_expediteur(email_exp, nom_exp, nom_voy, ville_dep, ville_dest):
    """Email à l'expéditeur : le voyageur a accepté sa demande."""
    _envoyer_email_async(
        sujet="✅ Votre demande a été acceptée !",
        message_texte=f"""
Bonjour {nom_exp},

Le voyageur {nom_voy} a accepté de transporter votre colis.

Trajet : {ville_dep} → {ville_dest}

Vous pouvez maintenant discuter avec lui dans votre espace connecté.

Cordialement,
L'équipe KERALINK
        """,
        destinataire=email_exp
    )


def email_refus_expediteur(email_exp, nom_exp, nom_voy, ville_dep, ville_dest):
    """Email à l'expéditeur : le voyageur a refusé sa demande."""
    _envoyer_email_async(
        sujet="❌ Votre demande a été refusée",
        message_texte=f"""
Bonjour {nom_exp},

Le voyageur {nom_voy} a refusé votre demande pour le trajet {ville_dep} → {ville_dest}.

Vous pouvez essayer avec d'autres voyageurs.

Cordialement,
L'équipe KERALINK
        """,
        destinataire=email_exp
    )


# ✅ SUPPRIMÉ : email_message_recu_expediteur — notifications de message désactivées
# ✅ SUPPRIMÉ : email_message_recu_voyageur  — notifications de message désactivées


def email_livraison_confirmee_expediteur(email_exp, nom_exp, nom_voy, ville_dep, ville_dest):
    """Email à l'expéditeur : le voyageur a confirmé la livraison."""
    _envoyer_email_async(
        sujet="📦 Votre colis a été livré — Confirmez la réception !",
        message_texte=f"""
Bonjour {nom_exp},

Le voyageur {nom_voy} a confirmé la livraison de votre colis.

Trajet : {ville_dep} → {ville_dest}

ACTION REQUISE : Connectez-vous à votre espace KERALINK pour :
1. Vérifier la photo de preuve de livraison
2. Confirmer la bonne réception de votre colis

Important : Si vous ne confirmez pas dans les 48 heures,
la plateforme débloquera automatiquement les gains du voyageur.
        """,
        destinataire=email_exp
    )


def email_gains_debloques_voyageur(email_voy, nom_voy, montant,
                                    debloque_par, ville_dep, ville_dest):
    """Email au voyageur : ses gains ont été débloqués (par admin)."""
    if debloque_par == 'Admin KERALINK':
        debloqueur_msg = "l'équipe KERALINK (délai 48h écoulé)"
    else:
        debloqueur_msg = f"l'expéditeur {debloque_par}"

    _envoyer_email_async(
        sujet="💰 Vos gains ont été débloqués sur KERALINK !",
        message_texte=f"""
Bonjour {nom_voy},

Excellente nouvelle ! Vos gains ont été débloqués et crédités sur votre portefeuille KERALINK.

Détails :
- Montant crédité : {float(montant):.2f} €
- Trajet : {ville_dep} → {ville_dest}
- Débloqué par : {debloqueur_msg}

Connectez-vous à votre espace KERALINK pour consulter votre portefeuille
et effectuer un retrait vers votre compte Orange Money, PayPal, Carte ou Wave.
        """,
        destinataire=email_voy
    )


def email_confirmation_reception_voyageur(email_voy, nom_voy, nom_exp,
                                           montant, ville_dep, ville_dest):
    """Email au voyageur : l'expéditeur a confirmé la réception, gains débloqués."""
    _envoyer_email_async(
        sujet="✅ Réception confirmée — Vos gains sont débloqués !",
        message_texte=f"""
Bonjour {nom_voy},

L'expéditeur {nom_exp} a confirmé la bonne réception de son colis.

Détails :
- Trajet : {ville_dep} → {ville_dest}
- Gains débloqués : {float(montant):.2f} €

Vos gains ont été crédités sur votre portefeuille KERALINK.
Connectez-vous pour effectuer un retrait vers votre compte
Orange Money, PayPal, Carte bancaire ou Wave.
        """,
        destinataire=email_voy
    )