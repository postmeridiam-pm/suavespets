from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.utils import timezone

def one_session_per_user(sender, user, request, **kwargs):
    # Obtiene todas las sesiones activas
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions:
        data = session.get_decoded()
        # Si la sesión pertenece al usuario actual, la elimina para forzar una sola sesión
        if data.get('_auth_user_id') == str(user.id_usuario):
            session.delete()

# Conectar la señal para que se ejecute al iniciar sesión un usuario
user_logged_in.connect(one_session_per_user)
