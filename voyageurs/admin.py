from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages as django_messages
from voyageurs.tasks import email_gains_debloques_voyageur 
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import path
from django.http import HttpResponse
from django.utils import timezone
from .models import (Voyageur, Expediteur, Demande, Transaction,
                     Matching, Profil, Message, MessageSupport,
                     Portefeuille, Retrait)                    

# ================================================================
# ✅ VUE ADMIN : Répondre au support
# ================================================================
def repondre_support_view(request, guest_id):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    if request.method == 'POST':
        contenu = request.POST.get('contenu', '').strip()
        if contenu:
            MessageSupport.objects.create(
                guest_id=guest_id,
                nom_complet='Admin KERALINK',
                type_profil='admin',
                sender='admin',
                contenu=contenu,
                lu=True
            )
        return redirect('/admin/voyageurs/messagesupport/')

    messages = MessageSupport.objects.filter(guest_id=guest_id).order_by('date')
    html = f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8">
    <title>Support — {guest_id[:8]}...</title>
    <style>
        body {{ font-family: sans-serif; max-width: 700px; margin: 30px auto; padding: 0 20px; }}
        .bubble {{ padding: 10px 14px; border-radius: 10px; margin: 8px 0; max-width: 80%; }}
        .user {{ background: #e3f2fd; align-self: flex-start; }}
        .admin {{ background: #e8f5e9; margin-left: auto; }}
        .wrap {{ display: flex; flex-direction: column; }}
        textarea {{ width: 100%; height: 80px; padding: 10px; border-radius: 8px; border: 1px solid #ddd; }}
        button {{ background: #0A1F44; color: white; border: none; padding: 10px 24px; border-radius: 8px; cursor: pointer; margin-top: 8px; }}
        .date {{ font-size: 0.75rem; color: #aaa; margin-top: 3px; }}
        h2 {{ color: #0A1F44; }}
        a {{ color: #FF7A00; }}
    </style></head><body>
    <a href="/admin/voyageurs/messagesupport/">← Retour</a>
    <h2>💬 Conversation support — {guest_id[:12]}...</h2>
    <div class="wrap">
    """
    for m in messages:
        css = 'admin' if m.sender == 'admin' else 'user'
        label = '👨‍💼 Admin' if m.sender == 'admin' else f'👤 {m.nom_complet}'
        html += f"""
        <div class="bubble {css}">
            <strong>{label}</strong><br>{m.contenu}
            <div class="date">{m.date.strftime('%d/%m/%Y à %H:%M')}</div>
        </div>"""
    html += f"""
    </div>
    <hr style="margin:20px 0;">
    <form method="post" action="/admin/support/repondre/{guest_id}/">
        <input type="hidden" name="csrfmiddlewaretoken" value="">
        <label><strong>Votre réponse :</strong></label><br>
        <textarea name="contenu" placeholder="Tapez votre réponse..."></textarea><br>
        <button type="submit">✉️ Envoyer la réponse</button>
    </form>
    <script>
        document.querySelector('input[name=csrfmiddlewaretoken]').value =
            document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    </script>
    </body></html>"""
    return HttpResponse(html)


# ================================================================
# ✅ ADMIN : Profil
# ================================================================
@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'username', 'type_profil_badge', 'email', 'telephone', 'date_creation')
    search_fields = ('nom_complet', 'username', 'email', 'telephone')
    list_filter = ('type_profil', 'date_creation')
    readonly_fields = ('date_creation', 'guest_id')
    ordering = ('-date_creation',)

    def type_profil_badge(self, obj):
        color = '#1E3A8A' if obj.type_profil == 'voyageur' else '#e65100'
        label = '🧳 Voyageur' if obj.type_profil == 'voyageur' else '📦 Expéditeur'
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:12px;font-size:0.85rem;">{}</span>',
            color, label
        )
    type_profil_badge.short_description = 'Type'


# ================================================================
# ✅ ADMIN : Voyageur
# ================================================================
@admin.register(Voyageur)
class VoyageurAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'telephone', 'trajet', 'poids_disponible',
                    'type_kg', 'statut_badge', 'is_matched', 'email', 'date_publication')
    search_fields = ('nom', 'prenom', 'telephone', 'ville_depart', 'ville_destination', 'email')
    list_filter = ('statut', 'is_matched', 'type_kg', 'date_publication')
    readonly_fields = ('date_publication', 'guest_id')
    ordering = ('-date_publication',)

    def trajet(self, obj):
        return format_html('<span style="color:#1E3A8A;">📍 {} → {}</span>',
                           obj.ville_depart, obj.ville_destination)
    trajet.short_description = 'Trajet'

    def statut_badge(self, obj):
        colors = {'actif': '#2e7d32', 'complet': '#f57f17', 'termine': '#c62828'}
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:12px;font-size:0.82rem;">{}</span>',
            colors.get(obj.statut, '#888'), obj.statut.upper()
        )
    statut_badge.short_description = 'Statut'


# ================================================================
# ✅ ADMIN : Expéditeur
# ================================================================
@admin.register(Expediteur)
class ExpediteurAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'telephone', 'trajet', 'poids_colis',
                    'prix_total', 'mode_paiement', 'paiement_badge', 'is_matched', 'email', 'date_demande')
    search_fields = ('nom', 'prenom', 'telephone', 'ville', 'ville_destination', 'email')
    list_filter = ('mode_paiement', 'paiement_effectue', 'is_matched', 'date_demande')
    readonly_fields = ('date_demande', 'guest_id', 'commission')
    ordering = ('-date_demande',)

    def trajet(self, obj):
        return format_html('<span style="color:#e65100;">📍 {} → {}</span>', obj.ville, obj.ville_destination)
    trajet.short_description = 'Trajet'

    def paiement_badge(self, obj):
        if obj.paiement_effectue:
            return format_html(
                '<span style="background:#2e7d32;color:white;padding:3px 10px;border-radius:12px;font-size:0.82rem;">✅ Payé</span>')
        return format_html(
            '<span style="background:#c62828;color:white;padding:3px 10px;border-radius:12px;font-size:0.82rem;">⏳ En attente</span>')
    paiement_badge.short_description = 'Paiement'


# ================================================================
# ✅ ADMIN : Matching
# ================================================================
@admin.register(Matching)
class MatchingAdmin(admin.ModelAdmin):
    list_display = ('id', 'expediteur_info', 'voyageur_info', 'statut_badge',
                    'livraison_confirmee_voyageur', 'photo_livraison_preview', 'date_creation')
    search_fields = ('expediteur__nom', 'expediteur__prenom', 'voyageur__nom', 'voyageur__prenom')
    list_filter = ('statut', 'livraison_confirmee_voyageur', 'date_creation')
    readonly_fields = ('date_creation', 'photo_livraison_grande')
    ordering = ('-date_creation',)

    fieldsets = (
        ('🔗 Participants', {'fields': ('expediteur', 'voyageur')}),
        ('📊 Statut', {'fields': ('statut', 'date_creation')}),
        ('📦 Livraison', {'fields': (
            'livraison_confirmee_voyageur', 'date_livraison',
            'photo_livraison', 'photo_livraison_grande'
        )}),
    )

    def expediteur_info(self, obj):
        return format_html(
            '<span style="color:#e65100;">📦 {} {}</span><br><small>{} → {}</small>',
            obj.expediteur.prenom, obj.expediteur.nom,
            obj.expediteur.ville, obj.expediteur.ville_destination
        )
    expediteur_info.short_description = 'Expéditeur'

    def voyageur_info(self, obj):
        return format_html(
            '<span style="color:#1E3A8A;">🧳 {} {}</span><br><small>{} → {}</small>',
            obj.voyageur.prenom, obj.voyageur.nom,
            obj.voyageur.ville_depart, obj.voyageur.ville_destination
        )
    voyageur_info.short_description = 'Voyageur'

    def statut_badge(self, obj):
        colors = {
            'confirme': '#1E3A8A', 'accepte': '#2e7d32',
            'refuse': '#c62828', 'en_attente': '#f57f17', 'livre': '#6a1b9a'
        }
        labels = {
            'confirme': '🔵 Confirmé', 'accepte': '✅ Accepté',
            'refuse': '❌ Refusé', 'en_attente': '⏳ En attente', 'livre': '📦 Livré'
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:12px;font-size:0.82rem;">{}</span>',
            colors.get(obj.statut, '#888'), labels.get(obj.statut, obj.statut)
        )
    statut_badge.short_description = 'Statut'

    def photo_livraison_preview(self, obj):
        if obj.photo_livraison:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="width:60px;height:60px;object-fit:cover;'
                'border-radius:6px;border:2px solid #2e7d32;">'
                '</a>',
                obj.photo_livraison.url, obj.photo_livraison.url
            )
        return format_html('<span style="color:#aaa;">Aucune photo</span>')
    photo_livraison_preview.short_description = '📷 Photo'

    def photo_livraison_grande(self, obj):
        if obj.photo_livraison:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width:400px;max-height:300px;'
                'object-fit:contain;border-radius:10px;border:2px solid #2e7d32;">'
                '</a><br><small style="color:#888;">Cliquer pour agrandir</small>',
                obj.photo_livraison.url, obj.photo_livraison.url
            )
        return format_html('<span style="color:#aaa;">Aucune photo.</span>')
    photo_livraison_grande.short_description = '📷 Aperçu grande'


# ================================================================
# ✅ ADMIN : Demande
# ================================================================
@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = ('expediteur', 'voyageur', 'statut_badge', 'date_creation', 'date_reponse')
    search_fields = ('expediteur__nom', 'voyageur__nom')
    list_filter = ('statut', 'date_creation')
    readonly_fields = ('date_creation',)
    ordering = ('-date_creation',)

    def statut_badge(self, obj):
        colors = {'en_attente': '#f57f17', 'accepte': '#2e7d32', 'refuse': '#c62828', 'termine': '#888'}
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:12px;font-size:0.82rem;">{}</span>',
            colors.get(obj.statut, '#888'), obj.statut.upper()
        )
    statut_badge.short_description = 'Statut'


# ================================================================
# ✅ ADMIN : Transaction — SÉPARATION gains voyageur / commissions admin
# ================================================================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'expediteur_info', 'voyageur_info',
                    'montant_total_formate', 'gains_voyageur_formate',
                    'commission_admin_formate', 'mode_paiement',
                    'statut_badge', 'debloque_par', 'date_transaction', 'actions_admin')
    search_fields = ('expediteur__nom', 'expediteur__prenom', 'voyageur__nom', 'voyageur__prenom')
    list_filter = ('mode_paiement', 'statut', 'date_transaction')
    readonly_fields = ('date_transaction', 'montant_voyageur', 'montant_commission')
    ordering = ('-date_transaction',)

    fieldsets = (
        ('💰 Répartition des montants', {
            'fields': ('montant', 'montant_voyageur', 'montant_commission', 'mode_paiement'),
            'description': (
                '💼 montant_voyageur = gains du voyageur (10€/kg) | '
                '🏢 montant_commission = revenus KERALINK (0.20€/kg)'
            )
        }),
        ('📊 Statut & Déblocage', {'fields': ('statut', 'debloque_par', 'note_remboursement', 'date_transaction')}),
        ('👥 Participants', {'fields': ('expediteur', 'voyageur')}),
    )

    def expediteur_info(self, obj):
        return format_html('<span style="color:#e65100;">📦 {} {}</span>',
                           obj.expediteur.prenom, obj.expediteur.nom)
    expediteur_info.short_description = 'Expéditeur'

    def voyageur_info(self, obj):
        if obj.voyageur:
            return format_html('<span style="color:#1E3A8A;">🧳 {} {}</span>',
                               obj.voyageur.prenom, obj.voyageur.nom)
        return format_html('<span style="color:#aaa;">—</span>')
    voyageur_info.short_description = 'Voyageur'

    def montant_total_formate(self, obj):
        return format_html(
            '<strong style="color:#0A1F44;font-size:0.95rem;">{} €</strong>',
            '{:.2f}'.format(obj.montant)
        )
    montant_total_formate.short_description = '💳 Total payé'

    def gains_voyageur_formate(self, obj):
        """✅ Gains destinés au voyageur (séparés des commissions)"""
        return format_html(
            '<strong style="color:#2e7d32;font-size:0.95rem;">{} €</strong>',
            '{:.2f}'.format(obj.montant_voyageur)
        )
    gains_voyageur_formate.short_description = '🧳 Gains voyageur'

    def commission_admin_formate(self, obj):
        """✅ Commission KERALINK = revenus admin (à retirer vers compte bancaire)"""
        return format_html(
            '<strong style="color:#FF7A00;font-size:0.95rem;">{} €</strong>',
            '{:.2f}'.format(obj.montant_commission)
        )
    commission_admin_formate.short_description = '🏢 Commission KERALINK'

    def statut_badge(self, obj):
        colors = {
            'en_attente': '#f57f17', 'bloque': '#1E3A8A',
            'debloque': '#2e7d32', 'rembourse': '#888',
            'remboursement_demande': '#c62828', 'echec': '#c62828'
        }
        labels = {
            'en_attente': '⏳ En attente', 'bloque': '🔒 Bloqué',
            'debloque': '✅ Débloqué', 'rembourse': '↩️ Remboursé',
            'remboursement_demande': '🔴 Remb. demandé', 'echec': '❌ Échec'
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:12px;font-size:0.82rem;">{}</span>',
            colors.get(obj.statut, '#888'), labels.get(obj.statut, obj.statut)
        )
    statut_badge.short_description = 'Statut'

    def actions_admin(self, obj):
        if obj.statut == 'bloque':
            montant_remb = '{:.2f}'.format(obj.montant_voyageur)
            return format_html(
                '<a href="/admin/voyageurs/transaction/{}/debloquer/" '
                'style="background:#2e7d32;color:white;padding:4px 10px;border-radius:6px;'
                'text-decoration:none;font-size:0.8rem;margin-right:4px;">💸 Débloquer</a>'
                '<a href="/admin/voyageurs/transaction/{}/rembourser/" '
                'style="background:#c62828;color:white;padding:4px 10px;border-radius:6px;'
                'text-decoration:none;font-size:0.8rem;">↩️ Rembourser {} €</a>',
                obj.id, obj.id, montant_remb
            )
        elif obj.statut == 'remboursement_demande':
            montant_remb = '{:.2f}'.format(obj.montant_voyageur)
            return format_html(
                '<a href="/admin/voyageurs/transaction/{}/rembourser/" '
                'style="background:#c62828;color:white;padding:4px 10px;border-radius:6px;'
                'text-decoration:none;font-size:0.8rem;">↩️ Rembourser {} €</a>',
                obj.id, montant_remb
            )
        elif obj.statut == 'debloque':
            return format_html('<span style="color:#2e7d32;">✅ Versé au voyageur</span>')
        elif obj.statut == 'rembourse':
            return format_html('<span style="color:#888;">↩️ Remboursé</span>')
        return format_html('<span style="color:#aaa;">—</span>')
    actions_admin.short_description = 'Actions'

    def changelist_view(self, request, extra_context=None):
        """✅ Tableau de bord financier séparé : gains voyageurs / commissions admin"""
        extra_context = extra_context or {}

        # ✅ Commissions KERALINK (revenus admin — à retirer vers compte bancaire)
        total_commission_debloque = Transaction.objects.filter(
            statut='debloque'
        ).aggregate(total=Sum('montant_commission'))['total'] or 0

        total_commission_bloque = Transaction.objects.filter(
            statut='bloque'
        ).aggregate(total=Sum('montant_commission'))['total'] or 0

        total_commission_all = Transaction.objects.exclude(
            statut__in=['echec']
        ).aggregate(total=Sum('montant_commission'))['total'] or 0

        # ✅ Gains voyageurs (versés aux voyageurs — pas des revenus admin)
        total_gains_voyageurs_debloque = Transaction.objects.filter(
            statut='debloque'
        ).aggregate(total=Sum('montant_voyageur'))['total'] or 0

        total_gains_voyageurs_bloque = Transaction.objects.filter(
            statut='bloque'
        ).aggregate(total=Sum('montant_voyageur'))['total'] or 0

        # ✅ Montants totaux
        total_bloque = Transaction.objects.filter(
            statut='bloque'
        ).aggregate(total=Sum('montant'))['total'] or 0

        total_debloque = Transaction.objects.filter(
            statut='debloque'
        ).aggregate(total=Sum('montant'))['total'] or 0

        total_rembourse = Transaction.objects.filter(
            statut='rembourse'
        ).aggregate(total=Sum('montant'))['total'] or 0

        extra_context.update({
            # Commissions admin
            'total_commission_debloque': '{:.2f}'.format(total_commission_debloque),
            'total_commission_bloque': '{:.2f}'.format(total_commission_bloque),
            'total_commission_all': '{:.2f}'.format(total_commission_all),
            # Gains voyageurs
            'total_gains_voyageurs_debloque': '{:.2f}'.format(total_gains_voyageurs_debloque),
            'total_gains_voyageurs_bloque': '{:.2f}'.format(total_gains_voyageurs_bloque),
            # Totaux
            'total_bloque': '{:.2f}'.format(total_bloque),
            'total_debloque': '{:.2f}'.format(total_debloque),
            'total_rembourse': '{:.2f}'.format(total_rembourse),
        })
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:transaction_id>/debloquer/',
                 self.admin_site.admin_view(self._debloquer_view),
                 name='transaction_debloquer'),
            path('<int:transaction_id>/rembourser/',
                 self.admin_site.admin_view(self._rembourser_view),
                 name='transaction_rembourser'),
        ]
        return custom_urls + urls

        
    def _debloquer_view(self, request, transaction_id):
        """
        Admin débloque manuellement les gains du voyageur.
        ✅ Crédite aussi la commission dans CompteCommission (revenus admin).
        """

        try:
            transaction = Transaction.objects.get(id=transaction_id)
            if transaction.statut == 'bloque':
                transaction.statut = 'debloque'
                transaction.debloque_par = 'Admin KERALINK'
                transaction.save()

                voyageur = transaction.voyageur
                if not voyageur:
                    matching = Matching.objects.filter(
                        expediteur=transaction.expediteur
                    ).first()
                    if matching:
                        voyageur = matching.voyageur

                if voyageur and voyageur.guest_id:
                    # ✅ Gains → portefeuille voyageur
                    portefeuille, _ = Portefeuille.objects.get_or_create(
                        guest_id=voyageur.guest_id,
                        defaults={'nom_complet': f"{voyageur.prenom} {voyageur.nom}"}
                    )
                    portefeuille.solde = round(
                        portefeuille.solde + transaction.montant_voyageur, 2
                    )
                    portefeuille.save()

                    # ✅ Commission → CompteCommission (revenus KERALINK séparés)
                    try:
                        from .models import CompteCommission
                        compte_comm, _ = CompteCommission.objects.get_or_create(
                            pk=1,
                            defaults={'solde_total': 0.0, 'solde_disponible': 0.0}
                        )
                        compte_comm.solde_total = round(
                            compte_comm.solde_total + transaction.montant_commission, 2
                        )
                        compte_comm.solde_disponible = round(
                            compte_comm.solde_disponible + transaction.montant_commission, 2
                        )
                        compte_comm.save()
                    except Exception:
                        pass  # CompteCommission optionnel — Retrait calcule en direct

                    # Email voyageur
                    try:
                        from voyageurs.views import _get_email_voyageur
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
                    except Exception:
                        pass

                django_messages.success(
                    request,
                    f"✅ Paiement {transaction_id} débloqué — "
                    f"Gains ({transaction.montant_voyageur:.2f} €) versés au voyageur. "
                    f"Commission ({transaction.montant_commission:.2f} €) créditée."
                )
        except Transaction.DoesNotExist:
            django_messages.error(request, "Transaction introuvable.")
        return redirect('/admin/voyageurs/transaction/')

    def _rembourser_view(self, request, transaction_id):
        """
        Admin valide un remboursement à l'expéditeur.
        ✅ La commission (0.20€/kg) est RETENUE — elle devient un revenu KERALINK débloqué.
        ✅ Seul le montant_voyageur est remboursé à l'expéditeur.
        ✅ La transaction passe en 'rembourse' → comptée dans commissions débloquées
           via la requête SQL dans RetraitAdmin.changelist_view.
        """
        from django.contrib import messages as django_messages
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            transaction.statut = 'rembourse'
            transaction.debloque_par = 'Admin KERALINK — Remboursement'
            transaction.save()

            # ✅ Commission retenue → créditée dans CompteCommission
            try:
                from .models import CompteCommission
                compte_comm, _ = CompteCommission.objects.get_or_create(
                    pk=1,
                    defaults={'solde_total': 0.0, 'solde_disponible': 0.0}
                )
                compte_comm.solde_total = round(
                    compte_comm.solde_total + transaction.montant_commission, 2
                )
                compte_comm.solde_disponible = round(
                    compte_comm.solde_disponible + transaction.montant_commission, 2
                )
                compte_comm.save()
            except Exception:
                pass

            django_messages.success(
                request,
                f"↩️ Transaction {transaction_id} remboursée. "
                f"Commission retenue : {transaction.montant_commission:.2f} €"
            )
        except Transaction.DoesNotExist:
            django_messages.error(request, "Transaction introuvable.")
        return redirect('/admin/voyageurs/transaction/')


# ================================================================
# ✅ ADMIN : Message
# ================================================================
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'expediteur', 'voyageur', 'sender_badge', 'contenu_short',
                    'photo_preview', 'est_photo_livraison', 'date')
    list_filter = ('sender', 'est_photo_livraison', 'date')
    search_fields = ('contenu', 'expediteur__nom', 'voyageur__nom')
    readonly_fields = ('date', 'photo_grande')
    ordering = ('-date',)

    def sender_badge(self, obj):
        if obj.sender == 'expediteur':
            return format_html(
                '<span style="background:#e65100;color:white;padding:2px 8px;border-radius:8px;font-size:0.8rem;">📦 Expéditeur</span>')
        return format_html(
            '<span style="background:#1E3A8A;color:white;padding:2px 8px;border-radius:8px;font-size:0.8rem;">🧳 Voyageur</span>')
    sender_badge.short_description = 'Expéditeur de'

    def contenu_short(self, obj):
        return (obj.contenu[:60] + '...') if len(obj.contenu) > 60 else obj.contenu
    contenu_short.short_description = 'Message'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="width:50px;height:50px;object-fit:cover;'
                'border-radius:4px;border:{};">'
                '</a>',
                obj.photo.url, obj.photo.url,
                '2px solid #2e7d32' if obj.est_photo_livraison else '1px solid #ddd'
            )
        return '—'
    photo_preview.short_description = '📷 Photo'

    def photo_grande(self, obj):
        if obj.photo:
            label = '📦 Photo de livraison' if obj.est_photo_livraison else '📷 Photo'
            return format_html(
                '<div><strong style="color:{};">{}</strong><br><br>'
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width:500px;border-radius:10px;border:2px solid {};">'
                '</a></div>',
                '#2e7d32' if obj.est_photo_livraison else '#555', label,
                obj.photo.url, obj.photo.url,
                '#2e7d32' if obj.est_photo_livraison else '#ddd'
            )
        return '—'
    photo_grande.short_description = 'Aperçu photo'


# ================================================================
# ✅ ADMIN : Support
# ================================================================
@admin.register(MessageSupport)
class MessageSupportAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'type_profil_badge', 'sender_badge',
                    'contenu_court', 'lu_badge', 'date', 'action_repondre')
    search_fields = ('nom_complet', 'contenu', 'guest_id')
    list_filter = ('sender', 'type_profil', 'lu', 'date')
    readonly_fields = ('date', 'guest_id', 'nom_complet', 'type_profil', 'sender')
    ordering = ('-date',)

    def type_profil_badge(self, obj):
        color = '#1E3A8A' if obj.type_profil == 'voyageur' else '#e65100'
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:10px;font-size:0.8rem;">{}</span>',
            color, obj.type_profil
        )
    type_profil_badge.short_description = 'Type'

    def sender_badge(self, obj):
        if obj.sender == 'admin':
            return format_html(
                '<span style="background:#1E3A8A;color:white;padding:2px 8px;border-radius:10px;font-size:0.8rem;">👨‍💼 Admin</span>')
        return format_html(
            '<span style="background:#FF7A00;color:white;padding:2px 8px;border-radius:10px;font-size:0.8rem;">👤 User</span>')
    sender_badge.short_description = 'De'

    def lu_badge(self, obj):
        if obj.lu:
            return format_html('<span style="color:#2e7d32;">✅ Lu</span>')
        return format_html('<span style="color:#c62828;font-weight:bold;">🔴 Non lu</span>')
    lu_badge.short_description = 'Lu'

    def contenu_court(self, obj):
        return (obj.contenu[:60] + '...') if len(obj.contenu) > 60 else obj.contenu
    contenu_court.short_description = 'Message'

    def action_repondre(self, obj):
        if obj.sender == 'user':
            return format_html(
                '<a href="/admin/support/repondre/{}/" '
                'style="background:#1E3A8A;color:white;padding:4px 10px;border-radius:6px;'
                'text-decoration:none;font-size:0.8rem;">✍️ Répondre</a>',
                obj.guest_id
            )
        return format_html('<span style="color:#aaa;">—</span>')
    action_repondre.short_description = 'Action'


# ================================================================
# ✅ ADMIN : Portefeuille voyageur (gains uniquement)
# ================================================================
@admin.register(Portefeuille)
class PortefeuilleAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'guest_id_court', 'solde_formate', 'date_mise_a_jour')
    search_fields = ('nom_complet', 'guest_id')
    ordering = ('-date_mise_a_jour',)
    readonly_fields = ('date_mise_a_jour', 'guest_id')

    def guest_id_court(self, obj):
        return (obj.guest_id[:12] + '...') if obj.guest_id else '—'
    guest_id_court.short_description = 'Guest ID'

    def solde_formate(self, obj):
        couleur = '#2e7d32' if obj.solde > 0 else '#888'
        return format_html(
            '<strong style="color:{};font-size:1rem;">{} €</strong>',
            couleur, '{:.2f}'.format(obj.solde)
        )
    solde_formate.short_description = '💰 Solde voyageur'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        total_soldes = Portefeuille.objects.aggregate(total=Sum('solde'))['total'] or 0
        extra_context['total_soldes_voyageurs'] = '{:.2f}'.format(total_soldes)
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Retrait)
class RetraitAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'type_retrait_badge', 'montant_formate',
                    'mode_retrait', 'coordonnees', 'statut_badge', 'date_demande', 'actions_retrait')
    search_fields = ('nom_complet', 'guest_id', 'coordonnees')
    list_filter = ('mode_retrait', 'statut', 'date_demande')
    readonly_fields = ('date_demande', 'guest_id')
    ordering = ('-date_demande',)
 
    def type_retrait_badge(self, obj):
        if obj.guest_id == 'ADMIN_KERALINK':
            return format_html(
                '<span style="background:#FF7A00;color:white;padding:4px 10px;'
                'border-radius:8px;font-size:0.82rem;">🏢 Commission Admin</span>'
            )
        return format_html(
            '<span style="background:#1E3A8A;color:white;padding:4px 10px;'
            'border-radius:8px;font-size:0.82rem;">🧳 Voyageur</span>'
        )
    type_retrait_badge.short_description = 'Type'
 
    def montant_formate(self, obj):
        # ✅ CORRECTION : pré-formater en Python, passer une string à format_html
        montant_str = "{:.2f}".format(float(obj.montant or 0))
        return format_html('<strong style="color:#1E3A8A;">{} €</strong>', montant_str)
    montant_formate.short_description = 'Montant'
 
    def statut_badge(self, obj):
        colors = {'en_attente': '#f57f17', 'traite': '#2e7d32', 'refuse': '#c62828'}
        labels = {'en_attente': '⏳ En attente', 'traite': '✅ Traité', 'refuse': '❌ Refusé'}
        color = colors.get(obj.statut, '#888')
        label = labels.get(obj.statut, obj.statut)
        return format_html(
            '<span style="background:{};color:white;padding:4px 10px;'
            'border-radius:8px;font-size:0.82rem;">{}</span>',
            color, label
        )
    statut_badge.short_description = 'Statut'
 
    def actions_retrait(self, obj):
        if obj.statut == 'en_attente':
            return format_html(
                '<a href="/admin/voyageurs/retrait/{}/traiter/" '
                'style="background:#2e7d32;color:white;padding:5px 10px;'
                'border-radius:6px;text-decoration:none;font-size:0.82rem;margin-right:4px;">'
                '✅ Traiter</a>'
                '<a href="/admin/voyageurs/retrait/{}/refuser/" '
                'style="background:#c62828;color:white;padding:5px 10px;'
                'border-radius:6px;text-decoration:none;font-size:0.82rem;">'
                '❌ Refuser</a>',
                obj.id, obj.id
            )
        elif obj.statut == 'traite':
            return format_html('<span style="color:#2e7d32;">✅ Traité</span>')
        return format_html('<span style="color:#c62828;">❌ Refusé</span>')
    actions_retrait.short_description = 'Action'
 
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # ✅ Commissions débloquées = statut 'debloque' OU 'rembourse'
        # - 'debloque' : livraison confirmée → gains voyageur versés, commission dégagée
        # - 'rembourse' : remboursement validé → commission retenue par KERALINK
        total_commissions_debloquees = float(
            Transaction.objects.filter(
                statut__in=['debloque', 'rembourse']  # ✅ LES DEUX CAS
            ).aggregate(total=Sum('montant_commission'))['total'] or 0
        )

        # Commissions encore bloquées (paiement en attente de livraison)
        total_commissions_bloquees = float(
            Transaction.objects.filter(
                statut='bloque'
            ).aggregate(total=Sum('montant_commission'))['total'] or 0
        )

        # Ce que l'admin a déjà retiré (historique des retraits commissions)
        total_deja_retire = float(
            Retrait.objects.filter(
                guest_id='ADMIN_KERALINK',
                statut='traite'
            ).aggregate(total=Sum('montant'))['total'] or 0
        )

        # Net disponible = débloqué - déjà retiré
        net_disponible = max(0.0, total_commissions_debloquees - total_deja_retire)

        extra_context.update({
            'total_commissions_debloquees': '{:.2f}'.format(total_commissions_debloquees),
            'total_commissions_bloquees':   '{:.2f}'.format(total_commissions_bloquees),
            'total_deja_retire':            '{:.2f}'.format(total_deja_retire),
            'net_disponible':               '{:.2f}'.format(net_disponible),
            'retrait_commissions_url': '/admin/voyageurs/retrait/retirer-commissions/',
        })

        return super().changelist_view(request, extra_context=extra_context)

 
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:retrait_id>/traiter/',
                self.admin_site.admin_view(self._traiter_view),
                name='retrait_traiter'
            ),
            path(
                '<int:retrait_id>/refuser/',
                self.admin_site.admin_view(self._refuser_view),
                name='retrait_refuser'
            ),
            path(
                'retirer-commissions/',
                self.admin_site.admin_view(self._retirer_commissions_view),
                name='retrait_commissions'
            ),
        ]
        return custom_urls + urls
 
    def _traiter_view(self, request, retrait_id):
        from django.contrib import messages
        try:
            retrait = Retrait.objects.get(id=retrait_id)
            retrait.statut = 'traite'
            retrait.date_traitement = timezone.now()
            retrait.save()
            messages.success(request, "✅ Retrait {} traité.".format(retrait_id))
        except Retrait.DoesNotExist:
            messages.error(request, "Retrait introuvable.")
        return redirect('/admin/voyageurs/retrait/')
 
    def _refuser_view(self, request, retrait_id):
        from django.contrib import messages
        try:
            retrait = Retrait.objects.get(id=retrait_id)
            # Rembourser le solde uniquement pour les voyageurs (pas les commissions admin)
            if retrait.guest_id != 'ADMIN_KERALINK':
                portefeuille = Portefeuille.objects.filter(guest_id=retrait.guest_id).first()
                if portefeuille:
                    portefeuille.solde += retrait.montant
                    portefeuille.save()
            retrait.statut = 'refuse'
            retrait.date_traitement = timezone.now()
            retrait.save()
            messages.success(request, "❌ Retrait {} refusé.".format(retrait_id))
        except Retrait.DoesNotExist:
            messages.error(request, "Retrait introuvable.")
        return redirect('/admin/voyageurs/retrait/')
 
    def _retirer_commissions_view(self, request):
        """
        ✅ Page de retrait des commissions KERALINK vers un compte bancaire international.
        Supporte Wise, Revolut, IBAN — conversion automatique de devise gérée par la banque.
        """
        from django.contrib import messages
 
        if request.method == 'POST':
            try:
                montant = float(request.POST.get('montant', 0))
            except (ValueError, TypeError):
                montant = 0
 
            mode = request.POST.get('mode_retrait', '').strip()
            coordonnees = request.POST.get('coordonnees', '').strip()
            devise_cible = request.POST.get('devise_cible', 'EUR').strip()
 
            if montant <= 0 or not mode or not coordonnees:
                messages.error(request, "⚠️ Tous les champs sont obligatoires.")
                return redirect('/admin/voyageurs/retrait/retirer-commissions/')
 
            # Commissions nettes disponibles
            total_commissions = float(
                Transaction.objects.filter(statut='debloque')
                .aggregate(total=Sum('montant_commission'))['total'] or 0
            )
            deja_retire = float(
                Retrait.objects.filter(guest_id='ADMIN_KERALINK', statut='traite')
                .aggregate(total=Sum('montant'))['total'] or 0
            )
            net_disponible = max(0.0, total_commissions - deja_retire)
 
            if montant > net_disponible:
                messages.error(
                    request,
                    "❌ Montant ({:.2f} €) supérieur au disponible ({:.2f} €).".format(
                        montant, net_disponible
                    )
                )
                return redirect('/admin/voyageurs/retrait/retirer-commissions/')
 
            Retrait.objects.create(
                guest_id='ADMIN_KERALINK',
                nom_complet='Admin KERALINK — Commission',
                montant=montant,
                mode_retrait=mode,
                coordonnees="{} | Devise cible: {}".format(coordonnees, devise_cible),
                statut='traite',
                date_traitement=timezone.now()
            )
            messages.success(
                request,
                "✅ {:.2f} € de commissions retirées vers {} ({}).".format(
                    montant, coordonnees, devise_cible
                )
            )
            return redirect('/admin/voyageurs/retrait/')
 
        # ===== PAGE GET : afficher le formulaire =====
        total_commissions = float(
            Transaction.objects.filter(statut='debloque')
            .aggregate(total=Sum('montant_commission'))['total'] or 0
        )
        total_bloquees = float(
            Transaction.objects.filter(statut='bloque')
            .aggregate(total=Sum('montant_commission'))['total'] or 0
        )
        deja_retire = float(
            Retrait.objects.filter(guest_id='ADMIN_KERALINK', statut='traite')
            .aggregate(total=Sum('montant'))['total'] or 0
        )
        net_disponible = max(0.0, total_commissions - deja_retire)
 
        # Pré-formater toutes les valeurs en Python — jamais de :.2f dans format_html
        tc  = "{:.2f}".format(total_commissions)
        tb  = "{:.2f}".format(total_bloquees)
        dr  = "{:.2f}".format(deja_retire)
        nd  = "{:.2f}".format(net_disponible)
 
        csrf_token = request.META.get('CSRF_COOKIE', '')
 
        html = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Retrait Commissions — KERALINK Admin</title>
<style>
  body {{ font-family:'Segoe UI',sans-serif; background:#f5f5f5;
          max-width:760px; margin:40px auto; padding:0 20px; color:#333; }}
  a {{ color:#FF7A00; text-decoration:none; font-size:0.9rem; }}
  h1 {{ color:#0A1F44; margin:16px 0 4px; font-size:1.5rem; }}
  p.sub {{ color:#888; font-size:0.88rem; margin-bottom:24px; }}
  .card {{ background:white; border-radius:12px; padding:24px;
           box-shadow:0 4px 16px rgba(0,0,0,0.08); margin-bottom:20px; }}
  .card h2 {{ color:#0A1F44; font-size:1rem; margin-bottom:16px;
              padding-bottom:10px; border-bottom:2px solid #FF7A00; }}
  .stat {{ display:flex; justify-content:space-between; align-items:center;
           padding:11px 0; border-bottom:1px solid #f0f0f0; font-size:0.9rem; }}
  .stat:last-child {{ border:none; }}
  .stat .val {{ font-weight:bold; font-size:1rem; }}
  .green {{ color:#2e7d32; }}
  .orange {{ color:#FF7A00; }}
  .blue {{ color:#1E3A8A; }}
  .red {{ color:#c62828; }}
  .highlight {{ background:#e8f5e9; border-radius:8px; padding:14px;
                margin-top:10px; display:flex; justify-content:space-between; }}
  .highlight .val {{ font-size:1.3rem; font-weight:900; color:#2e7d32; }}
  label {{ display:block; font-size:0.85rem; font-weight:600;
           color:#555; margin:14px 0 6px; }}
  input, select {{ width:100%; padding:11px 14px; border-radius:8px;
                   border:1.5px solid #e0e0e0; font-size:0.95rem;
                   outline:none; box-sizing:border-box; }}
  input:focus, select:focus {{ border-color:#FF7A00; }}
  .notice {{ background:#e3f2fd; border-radius:8px; padding:12px 16px;
             font-size:0.85rem; color:#1565c0; margin:12px 0; line-height:1.6; }}
  .warn {{ background:#fff3e0; border-radius:8px; padding:12px 16px;
           font-size:0.85rem; color:#e65100; margin:12px 0; line-height:1.6; }}
  button {{ background:linear-gradient(90deg,#FF7A00,#e66900); color:white;
            border:none; padding:14px; border-radius:10px; font-size:1rem;
            font-weight:bold; width:100%; cursor:pointer; margin-top:8px; }}
  button:hover {{ opacity:0.92; }}
</style>
</head>
<body>
<a href="/admin/voyageurs/retrait/">← Retour aux retraits</a>
<h1>🏢 Retrait des Commissions KERALINK</h1>
<p class="sub">Transférez vos commissions vers votre compte bancaire international
— conversion automatique dans la devise de votre choix (Wise, Revolut, IBAN).</p>
 
<div class="card">
  <h2>📊 État des commissions</h2>
  <div class="stat">
    <span>✅ Commissions débloquées (brut cumulé)</span>
    <span class="val green">{tc} €</span>
  </div>
  <div class="stat">
    <span>🔒 Commissions encore bloquées</span>
    <span class="val blue">{tb} €</span>
  </div>
  <div class="stat">
    <span>💸 Déjà retiré (historique)</span>
    <span class="val orange">{dr} €</span>
  </div>
  <div class="highlight">
    <span style="font-weight:600;">💰 Net disponible à retirer</span>
    <span class="val">{nd} €</span>
  </div>
</div>
 
<div class="card">
  <h2>💸 Effectuer un retrait</h2>
 
  <div class="notice">
    ℹ️ <strong>Conversion multi-devises automatique :</strong><br>
    Wise et Revolut Business acceptent les virements en EUR et les convertissent
    automatiquement dans la devise cible de votre compte (USD, XOF, MAD, GBP, TND, etc.)
    au taux du marché, sans frais cachés.
  </div>
 
  <div class="warn">
    ⚠️ Seul le <strong>net disponible ({nd} €)</strong> est retirable.
    Les commissions encore bloquées ({tb} €) seront disponibles
    après confirmation des livraisons par les expéditeurs.
  </div>
 
  <form method="post" action="/admin/voyageurs/retrait/retirer-commissions/">
    <input type="hidden" name="csrfmiddlewaretoken" id="csrf-field" value="">
 
    <label>Montant à retirer (€) — max {nd} €</label>
    <input type="number" name="montant" step="0.01" min="0.01"
           max="{nd}" value="{nd}" required>
 
    <label>Mode de transfert international</label>
    <select name="mode_retrait">
      <option value="wise">🌍 Wise (multi-devises, taux marché — recommandé)</option>
      <option value="revolut">💜 Revolut Business</option>
      <option value="virement">🏦 Virement SEPA (IBAN)</option>
      <option value="paypal">🅿️ PayPal Business</option>
      <option value="stripe">💳 Stripe (compte marchand)</option>
    </select>
 
    <label>Devise cible de votre compte bancaire</label>
    <select name="devise_cible">
      <option value="EUR">🇪🇺 EUR — Euro</option>
      <option value="USD">🇺🇸 USD — Dollar américain</option>
      <option value="GBP">🇬🇧 GBP — Livre sterling</option>
      <option value="XOF">🌍 XOF — Franc CFA (UEMOA)</option>
      <option value="MAD">🇲🇦 MAD — Dirham marocain</option>
      <option value="TND">🇹🇳 TND — Dinar tunisien</option>
      <option value="DZD">🇩🇿 DZD — Dinar algérien</option>
      <option value="CAD">🇨🇦 CAD — Dollar canadien</option>
      <option value="CHF">🇨🇭 CHF — Franc suisse</option>
      <option value="XAF">🌍 XAF — Franc CFA (CEMAC)</option>
    </select>
 
    <label>Coordonnées de réception (IBAN, email Wise/Revolut...)</label>
    <input type="text" name="coordonnees"
           placeholder="Ex: FR76 3000 4028 37... ou admin@keralink.com (Wise)"
           required>
 
    <button type="submit">💸 Retirer les commissions</button>
  </form>
</div>
 
<script>
  // Injecter le CSRF token depuis le cookie
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  if (match) document.getElementById('csrf-field').value = match[1];
</script>
</body>
</html>""".format(tc=tc, tb=tb, dr=dr, nd=nd)
 
        return HttpResponse(html)