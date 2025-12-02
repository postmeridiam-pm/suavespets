from django.apps import AppConfig

class AppSuavesPetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appsuavespets'

    def ready(self):
        # Importa el módulo signals cuando la app está lista
        import appsuavespets.signals
