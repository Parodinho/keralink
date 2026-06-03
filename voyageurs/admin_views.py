from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .models import MessageSupport


@staff_member_required
def repondre_support(request, guest_id):
    messages = MessageSupport.objects.filter(guest_id=guest_id).order_by('date')
    user_msg = messages.filter(sender='user').first()
    nom = user_msg.nom_complet if user_msg else 'Utilisateur'

    if request.method == 'POST':
        contenu = request.POST.get('contenu', '').strip()
        if contenu:
            MessageSupport.objects.create(
                guest_id=guest_id,
                nom_complet='Admin KERALINK',
                type_profil='admin',
                sender='admin',
                contenu=contenu,
                lu=False
            )
        return redirect(f'/admin/support/repondre/{guest_id}/')

    return render(request, 'voyageurs/admin_support.html', {
        'messages': messages,
        'guest_id': guest_id,
        'nom_utilisateur': nom,
    })