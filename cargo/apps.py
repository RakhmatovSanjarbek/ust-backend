import firebase_admin
from firebase_admin import credentials
from django.apps import AppConfig


class CargoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cargo'

    def ready(self):
        import cargo.models  # signallarni yuklash

        try:
            firebase_admin.get_app()
        except ValueError:
            from django.conf import settings
            cred_path = str(settings.FIREBASE_CREDENTIALS_PATH)
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"[Firebase] ✅ SDK ishga tushirildi: {cred_path}")