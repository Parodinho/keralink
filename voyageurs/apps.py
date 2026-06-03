from django.apps import AppConfig

class VoyageursConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'voyageurs'

    def ready(self):
        import voyageurs.signals  # Active le signal