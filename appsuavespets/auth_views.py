from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from django.contrib.auth.hashers import check_password
from .forms import RegistroForm
from .models import Usuario


def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_user = authenticate(request, email=user.email, password=form.cleaned_data.get('password'))
            if auth_user is not None:
                login(request, auth_user)
                messages.success(request, 'Registro exitoso.')
                return redirect('listado_pets')
            messages.success(request, 'Registro exitoso. Inicia sesión.')
            return redirect('login')
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = RegistroForm()
    return render(request, 'templatesApp/registro/registro.html', {'form': form})


def login_view(request):
    last_email = request.COOKIES.get('last_email', '')
    intentos = request.session.get('login_intentos', 0)
    # Limpiar mensajes antiguos al mostrar el login
    if request.method == 'GET':
        for _ in messages.get_messages(request):
            pass
    if intentos >= 5:
        messages.error(request, 'Demasiados intentos. Intenta más tarde.')
        return render(request, 'templatesApp/registro/login.html', {'last_email': last_email})
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        password = request.POST.get('password') or ''
        remember_me = request.POST.get('remember_me')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            request.session['login_intentos'] = 0
            next_url = request.GET.get('next')
            target = next_url or 'listado_pets'
            response = redirect(target)
            if remember_me:
                response.set_cookie('last_email', email, max_age=30*24*60*60, secure=not settings.DEBUG, httponly=True, samesite='Lax')
            else:
                response.delete_cookie('last_email')
            return response
        request.session['login_intentos'] = intentos + 1
        messages.error(request, 'Email o contraseña incorrectos.')
    return render(request, 'templatesApp/registro/login.html', {'last_email': last_email})

def logout_view(request):
    logout(request)
    return redirect('login')


def acceso_denegado(request):
    return render(request, 'templatesApp/registro/acceso-denegado.html')

# eliminado duplicado de registro_view (se usa el definido arriba)


# eliminado duplicado de login_view


def logout_view(request):
    logout(request)
    return redirect('login')


def acceso_denegado(request):
    return render(request, 'templatesApp/registro/acceso-denegado.html')
