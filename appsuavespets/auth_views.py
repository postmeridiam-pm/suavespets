from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password
from .forms import RegistroForm
from .models import Usuario


def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registro exitoso.')
            return redirect('login')
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = RegistroForm()
    return render(request, 'templatesApp/registro/registro.html', {'form': form})


def login_view(request):
    last_email = request.COOKIES.get('last_email', '')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        user = None
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            user = None
        if user and check_password(password, user.password):
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            response = redirect('inicio')
            if remember_me:
                response.set_cookie('last_email', email, max_age=30*24*60*60)
            else:
                response.delete_cookie('last_email')
            return response
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
