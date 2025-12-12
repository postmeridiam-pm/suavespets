from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Usuario, Pet, EventoClinico, Cuidados
from appsuavespets.views import is_admin
from django import forms

@login_required
@user_passes_test(is_admin)
def admin_configuracion(request):
    total_mascotas = Pet.objects.filter(Q(is_deleted=0) | Q(is_deleted__isnull=True)).count()
    total_eventos = EventoClinico.objects.filter(Q(is_deleted=0) | Q(is_deleted__isnull=True)).count()
    veterinarios = Usuario.objects.filter(tipo_usuario='veterinario').count()
    socios = Usuario.objects.filter(tipo_usuario='socio').count()
    total_cuidados = Cuidados.objects.filter(Q(is_deleted=0) | Q(is_deleted__isnull=True)).count()

    context = {
        'total_mascotas': total_mascotas,
        'total_eventos': total_eventos,
        'veterinarios': veterinarios,
        'socios': socios,
        'total_cuidados': total_cuidados,
    }
    return render(request, 'templatesApp/configuracion/admin-configuracion.html', context)

@login_required
def mis_permisos(request):
    return render(request, 'templatesApp/configuracion/permisos.html')

@login_required
@user_passes_test(is_admin)
def gestionar_usuarios(request):
    usuarios = Usuario.objects.all()
    return render(request, 'templatesApp/configuracion/gestionar_usuarios.html', {'usuarios': usuarios})

@login_required
@user_passes_test(is_admin)
def asignar_rol(request, user_id):
    usuario = get_object_or_404(Usuario, pk=user_id)
    if request.method == 'POST':
        nuevo_rol = request.POST.get('nuevo_rol')
        if nuevo_rol in ['veterinario', 'clinica', 'colaborador', 'socio', 'socio_premium', 'invitado', 'admin']:
            usuario.tipo_usuario = nuevo_rol
            usuario.save()
            messages.success(request, 'Rol asignado.')
            return redirect('gestionar_usuarios')
        else:
            messages.error(request, 'Debes seleccionar un rol válido.')
    return render(request, 'templatesApp/configuracion/asignar_rol.html', {'usuario': usuario})

@login_required
def cambiar_contrasena(request):
    return render(request, 'templatesApp/configuracion/cambiar-contrasena.html')

@login_required
def preferencias(request):
    return render(request, 'templatesApp/configuracion/preferencias.html')


# Creación de usuarios especiales (solo admin)
@login_required
@user_passes_test(is_admin)
def crear_usuario_especial(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        dni = request.POST.get('dni')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        tipo = request.POST.get('tipo_usuario')
        password = request.POST.get('password')

        if tipo not in ['veterinario', 'clinica', 'colaborador']:
            messages.error(request, 'Tipo de usuario no permitido para este registro.')
            return redirect('panel_configuracion')

        if not all([nombre, email, password]):
            messages.error(request, 'Completa los campos obligatorios.')
            return redirect('panel_configuracion')

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe un usuario con ese email.')
            return redirect('panel_configuracion')

        usuario = Usuario(nombre=nombre, dni=dni or '', email=email, telefono=telefono or '', tipo_usuario=tipo)
        usuario.set_password(password)
        usuario.save()
        messages.success(request, 'Usuario creado correctamente.')
        return redirect('gestionar_usuarios')

    return render(request, 'templatesApp/configuracion/crear_usuario_especial.html')
