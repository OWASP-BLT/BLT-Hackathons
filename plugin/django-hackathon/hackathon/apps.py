from django.apps import AppConfig


class HackathonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hackathon"
    verbose_name = "Hackathon Management"
    
    def ready(self):
        # Import signal handlers if any
        pass