from django.apps import AppConfig


class UnassignedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'unassigned'
    verbose_name = 'Kodsiz tovarlar'