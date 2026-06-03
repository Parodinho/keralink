from django.contrib import admin
from django.urls import path, include
from voyageurs.admin_views import repondre_support
from voyageurs import views as voyageurs_views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/support/repondre/<str:guest_id>/', repondre_support, name='repondre_support'),
    path('admin/voyageurs/transaction/<int:transaction_id>/debloquer/', voyageurs_views.debloquer_paiement_admin, name='debloquer_paiement_admin'),
    path('admin/voyageurs/transaction/<int:transaction_id>/rembourser/', voyageurs_views.rembourser_admin, name='rembourser_admin'),
    path('admin/', admin.site.urls),
    path('admin/voyageurs/retrait/<int:retrait_id>/traiter/', voyageurs_views.traiter_retrait_admin, name='traiter_retrait_admin'),
    path('admin/voyageurs/retrait/<int:retrait_id>/refuser/', voyageurs_views.refuser_retrait_admin, name='refuser_retrait_admin'),
    path('accounts/', include('allauth.urls')),   # ← NOUVEAU
    path('google-callback/', voyageurs_views.google_callback, name='google_callback'),  # ← NOUVEAU
    path('', include('voyageurs.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)