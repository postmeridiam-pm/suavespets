from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from .forms import PetForm, PetUpdateForm, EditarPerfilForm, RegistroForm
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import PetSerializer
from django.http import JsonResponse
from functools import wraps
from appsuavespets.models import ArchivoAdjunto, EventoClinico, Usuario, Pet, Notificacion
from django.contrib.auth import login
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from appsuavespets.services.gemini_service import GeminiVetService
import requests
import logging
import uuid
from decimal import Decimal, InvalidOperation
from .models import Pet, Cuidados


logger = logging.getLogger(__name__)

from django.contrib import messages
from django.utils import timezone
from .models import Pet, Cuidados, EventoClinico


# ============================================
# PÁGINA DE INICIO PÚBLICA
# ============================================
def inicio(request):
    """Página de inicio pública"""
    return render(request, 'templatesApp/inicio.html')


# ============================================
# REGISTRO Y AUTENTICACIÓN
# ============================================
def registro(request):
    """Registro de nuevos usuarios con validación robusta"""
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        
        try:
            if form.is_valid():
                user = form.save()
                messages.success(request, '✅ Usuario creado exitosamente.')
                logger.info(f'Usuario registrado: {user.email}')
                return redirect('login')
            else:
                # Mostrar errores específicos
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')
                logger.warning(f'Registro fallido: {form.errors}')
        
        except IntegrityError as e:
            logger.error(f'Error de integridad en registro: {e}')
            messages.error(request, '❌ Este email o identificación ya está registrado.')
        
        except Exception as e:
            logger.error(f'Error inesperado en registro: {e}')
            messages.error(request, '❌ Error al registrar. Intenta nuevamente.')
    
    else:
        form = RegistroForm()
    
    return render(request, 'templatesApp/registro.html', {'form': form})


def iniciar_sesion(request):
    """Login con control de intentos fallidos"""
    # Control de intentos fallidos
    intentos = request.session.get('login_intentos', 0)
    
    if intentos >= 5:
        messages.error(request, '❌ Demasiados intentos fallidos. Intenta en 15 minutos.')
        return render(request, 'templatesApp/login.html')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, '❌ Email y contraseña son obligatorios.')
            return render(request, 'templatesApp/login.html')
        
        try:
            user = Usuario.objects.get(email=email)
            
            if user and check_password(password, user.hash_contrasenia):
                login(request, user)
                
                # Resetear intentos fallidos
                request.session['login_intentos'] = 0
                
                logger.info(f'Login exitoso: {user.email}')
                return redirect('inicio')
            else:
                # Incrementar intentos fallidos
                request.session['login_intentos'] = intentos + 1
                messages.error(request, '❌ Email o contraseña incorrectos.')
                logger.warning(f'Login fallido para: {email}')
        
        except Usuario.DoesNotExist:
            request.session['login_intentos'] = intentos + 1
            messages.error(request, '❌ Email o contraseña incorrectos.')
            logger.warning(f'Login fallido - usuario no existe: {email}')
        
        except Exception as e:
            logger.error(f'Error inesperado en login: {e}')
            messages.error(request, '❌ Error al iniciar sesión.')
    
    return render(request, 'templatesApp/login.html')


# ============================================
# DECORADOR PARA ROLES
# ============================================
def role_required(allowed_roles):
    """Decorador para verificar roles de usuario"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if hasattr(request.user, 'tipo_usuario'):
                tu = request.user.tipo_usuario
                if tu == 'admin' or tu in allowed_roles:
                    return view_func(request, *args, **kwargs)
            messages.error(request, '❌ No tienes permiso para acceder a esta página.')
            return redirect('acceso_denegado')
        return _wrapped_view
    return decorator


def is_admin(user):
    """Verifica si el usuario es admin"""
    return hasattr(user, 'tipo_usuario') and user.tipo_usuario == 'admin'


# ============================================
# PERFIL DE USUARIO
# ============================================
@login_required
def perfil(request):
    """Perfil del usuario"""
    return render(request, 'templatesApp/perfiles/perfil.html', {'user': request.user})


@login_required
def editar_perfil(request):
    """Editar perfil del usuario con validación"""
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user)
        
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "✅ Perfil actualizado correctamente.")
                logger.info(f'Perfil actualizado: {request.user.email}')
                return redirect('perfil')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')
        
        except IntegrityError as e:
            logger.error(f'Error de integridad al actualizar perfil: {e}')
            messages.error(request, '❌ Error: Email ya está en uso.')
        
        except Exception as e:
            logger.error(f'Error al actualizar perfil: {e}')
            messages.error(request, '❌ Error al actualizar perfil.')
    
    else:
        form = EditarPerfilForm(instance=request.user)
    
    return render(request, 'templatesApp/perfiles/editar_perfil.html', {'form': form})


# ============================================
# CRUD MASCOTAS (PETS)
# ============================================
@login_required
def listado_pets(request):
    if request.user.tipo_usuario == 'admin' or request.user.is_staff:
        pets = Pet.objects.filter(Q(is_deleted=0) | Q(is_deleted__isnull=True))
    else:
        pets = Pet.objects.filter(responsable_id=request.user.id_usuario).filter(Q(is_deleted=0) | Q(is_deleted__isnull=True))
    
    return render(request, 'templatesApp/pets/listado-pets.html', {'pets': pets})

from .models import Pet

@login_required
@role_required(['socio', 'socio_premium'])
def detalle_pet(request, pk):
    # Obtener la mascota, verificando si es administrador o responsable
    if is_admin(request.user):
        pet = get_object_or_404(Pet, pk=pk)
    else:
        pet = get_object_or_404(Pet, pk=pk, responsable=request.user)

    # Obtener información veterinaria generada con IA usando Gemini
    info_vet = GeminiVetService.get_pet_health_info(pet)
    if not info_vet or not any(info_vet.get(k) for k in ['enfermedades','alimentos_prohibidos','cuidados','estudios','referencias']):
        especie = (pet.especie or '').lower()
        if especie == 'perro':
            info_vet = {
                'enfermedades': '- Parvovirus: prevenir con calendario de vacunas\n- Moquillo: vacunación y controles regulares\n- Tos de las perreras: evitar contagios en guarderías\n- Leptospirosis: evitar aguas estancadas y mantener vacunación\n- Otitis: revisar y limpiar orejas periódicamente',
                'alimentos_prohibidos': '- Chocolate: puede causar problemas serios\n- Uvas y pasas: pueden afectar los riñones\n- Cebolla y ajo: pueden alterar la sangre\n- Alcohol: nocivo para su salud\n- Xilitol: puede bajar el azúcar peligrosamente',
                'cuidados': '- Vacunas y desparasitación al día\n- Higiene dental mensual\n- Ejercicio diario acorde al tamaño\n- Protección contra parásitos externos\n- Controles veterinarios cada 6-12 meses',
                'estudios': '- Hemograma anual en adultos\n- Radiografías si hay cojera\n- Perfil renal/hepático en mayores de 7 años',
                'referencias': '- AVMA. (2015). Preventive Care.\n- WSAVA. (2020). Vaccination Guidelines.'
            }
        elif especie == 'gato':
            info_vet = {
                'enfermedades': '- Panleucopenia: prevenir con vacunación completa\n- Rinotraqueitis: medidas de higiene y vacunas\n- Gingivitis: higiene dental y controles\n- Obesidad: alimentación adecuada y juego diario\n- Enfermedad renal crónica: monitoreo especialmente en mayores',
                'alimentos_prohibidos': '- Chocolate: puede afectar su salud\n- Cebolla y ajo: pueden alterar la sangre\n- Lácteos: suelen causar molestias digestivas\n- Atún crudo: puede causar déficit de vitaminas\n- Huesos: riesgo de lesiones',
                'cuidados': '- Vacunación core y refuerzos\n- Enriquecimiento ambiental diario\n- Higiene dental y dieta adecuada\n- Control de parásitos internos/externos',
                'estudios': '- Hemograma y bioquímica anual\n- Estudios cardíacos si hay soplo\n- Uroanálisis desde los 7 años',
                'referencias': '- AAFP. (2018). Feline Preventive Care.\n- ISFM. (2019). Senior Cat Guidelines.'
            }
        else:
            info_vet = {
                'enfermedades': '- Enfermedades comunes según especie\n- Consulta profesional recomendada',
                'alimentos_prohibidos': '- Evitar tóxicos conocidos\n- Dieta específica por especie',
                'cuidados': '- Calendario de vacunas y desparasitación\n- Controles periódicos',
                'estudios': '- Pruebas básicas según edad',
                'referencias': '- Guías veterinarias generales.'
            }

    # Renderizar la plantilla pasando pet e info_vet al contexto
    return render(request, 'templatesApp/pets/detalle-pet.html', {
        'pet': pet,
        'info_vet': info_vet,
    })



@login_required
@role_required(['socio', 'socio_premium'])
def agregar_pet(request):
    """Agregar nueva mascota con validación robusta"""
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES)
        
        try:
            if form.is_valid():
                with transaction.atomic():
                    pet = form.save(commit=False)
                    pet.responsable = request.user
                    pet.es_mestizo = 1 if request.POST.get('es_mestizo') else 0
                    
                    # Generar número de ficha único si no existe
                    if not pet.numero_ficha:
                        pet.numero_ficha = f'PET-{uuid.uuid4().hex[:8].upper()}'
                    
                    # Guardar foto si se envió
                    if 'foto_url' in request.FILES:
                        pet.foto_url = request.FILES['foto_url']
                    pet.save()
                    
                    messages.success(
                        request,
                        f'✅ {pet.nombre_pet} registrado exitosamente con ficha #{pet.numero_ficha}'
                    )
                    logger.info(f'Pet creado: {pet.id_pet} por usuario {request.user.id_usuario}')
                    return redirect('detalle_pet', pk=pet.id_pet)
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')
                logger.warning(f'Formulario pet inválido: {form.errors}')
        
        except IntegrityError as e:
            logger.error(f'Error de integridad al crear pet: {e}')
            messages.error(request, '❌ Error: Ya existe una mascota con ese número de ficha.')
        
        except Exception as e:
            logger.error(f'Error inesperado al crear pet: {e}')
            messages.error(request, '❌ Ocurrió un error inesperado. Intenta nuevamente.')
    
    else:
        form = PetForm()
    
    return render(request, 'templatesApp/pets/agregar-pet.html', {'form': form})

@api_view(['POST'])
@csrf_exempt
def agregar_pet_api(request):
    try:
        # Obtener datos del formulario
        nombre_pet = request.data.get('nombre_pet')
        descripcion_pet = request.data.get('descripcion_pet')
        especie = request.data.get('especie')
        sexo = request.data.get('sexo')
        tamanio = request.data.get('tamanio')
        raza = request.data.get('raza')
        es_mestizo = request.data.get('es_mestizo', '0') == '1'
        peso_kg = request.data.get('peso_kg')
        edad = request.data.get('edad')
        fecha_nacimiento = request.data.get('fecha_nacimiento')
        alergias = request.data.get('alergias')
        numero_ficha = request.data.get('numero_ficha')
        
        # Obtener archivo de foto
        foto = request.FILES.get('foto')
        
        # Validaciones básicas
        if not nombre_pet or not especie or not sexo or not tamanio:
            return Response({'error': 'Faltan campos obligatorios'}, status=400)
        
        # Crear instancia de Pet
        pet = Pet(
            nombre_pet=nombre_pet,
            descripcion_pet=descripcion_pet,
            especie=especie,
            sexo=sexo,
            tamanio=tamanio,
            raza=raza if raza else None,
            es_mestizo=es_mestizo,
            peso_kg=float(peso_kg) if peso_kg else None,
            edad=int(edad) if edad else None,
            fecha_nacimiento=fecha_nacimiento if fecha_nacimiento else None,
            alergias=alergias if alergias else None,
            numero_ficha=numero_ficha,
            responsable_id=request.user.id_usuario,
            is_deleted=0
        )
        
        pet.save()
        
        if foto:
            pet.foto = foto
            pet.save()
        
        return Response({
            'success': True,
            'message': 'Mascota registrada exitosamente',
            'id_pet': pet.id_pet
        }, status=201)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@login_required
@role_required(['socio', 'socio_premium', 'veterinario'])
def actualizar_pet(request, pk):
    """Actualizar información de mascota"""
    try:
        if is_admin(request.user):
            pet = get_object_or_404(Pet, id_pet=pk, is_deleted=0)
        elif request.user.tipo_usuario == 'veterinario':
            pet = get_object_or_404(Pet, id_pet=pk, veterinario_id=request.user.id_usuario, is_deleted=0)
            consent = request.GET.get('consent') == '1'
            if not consent:
                messages.error(request, 'Se requiere consentimiento previo del responsable para editar.')
                return redirect('detalle_pet', pk=pk)
        else:
            pet = get_object_or_404(Pet, id_pet=pk, responsable_id=request.user.id_usuario, is_deleted=0)
        
        if request.method == 'POST':
            # Actualizar campos básicos
            pet.nombre_pet = request.POST.get('nombre_pet')
            pet.especie = request.POST.get('especie')
            pet.raza = request.POST.get('raza')
            pet.sexo = request.POST.get('sexo')
            pet.tamanio = request.POST.get('tamanio')
            pet.descripcion_pet = request.POST.get('descripcion_pet', '')
            
            # Campos opcionales
            edad = request.POST.get('edad')
            pet.edad = int(edad) if edad else None
            
            peso = request.POST.get('peso_kg')
            pet.peso_kg = float(peso) if peso else None
            
            fecha_nac = request.POST.get('fecha_nacimiento')
            pet.fecha_nacimiento = fecha_nac if fecha_nac else None
            
            pet.alergias = request.POST.get('alergias', '')
            pet.es_mestizo = 1 if request.POST.get('es_mestizo') else 0
            pet.otra_raza = request.POST.get('otra_raza', '')
            
            # Manejo de foto
            if 'foto_url' in request.FILES:
                pet.foto_url = request.FILES['foto_url']
            
            pet.fecha_actualizacion = timezone.now()
            pet.save()
            
            messages.success(request, f'✅ {pet.nombre_pet} actualizado correctamente.')
            return redirect('detalle_pet', pk=pk)
        
        return render(request, 'templatesApp/pets/actualizar-pet.html', {
            'pet': pet
        })
    
    except Pet.DoesNotExist:
        messages.error(request, '❌ Mascota no encontrada.')
        return redirect('listado_pets')
    
    except Exception as e:
        logger.error(f'Error al actualizar pet: {e}')
        messages.error(request, '❌ Error al actualizar la mascota.')
        return redirect('listado_pets')

@login_required
@role_required(['socio', 'socio_premium'])
def remover_pet(request, pk):
    """Remover mascota (soft delete)"""
    try:
        if is_admin(request.user):
            pet = get_object_or_404(Pet, pk=pk)
        else:
            pet = get_object_or_404(Pet, pk=pk, responsable_id=request.user.id_usuario)
        if pet.is_deleted:
            messages.error(request, '❌ La mascota ya está removida.')
            return redirect('listado_pets')
        
        if request.method == 'POST':
            with transaction.atomic():
                motivo = request.POST.get('motivo', '').strip()
                pet.is_deleted = 1
                pet.save()
                
                messages.success(request, f'✅ {pet.nombre_pet} removida correctamente del listado.')
                logger.info(f'Pet removida (soft): {pet.id_pet} por usuario {request.user.id_usuario}. Motivo: {motivo}')
                return redirect('listado_pets')
        
        return render(request, 'templatesApp/pets/remover-pet.html', {'pet': pet})
    
    except Pet.DoesNotExist:
        messages.error(request, '❌ Mascota no encontrada.')
        return redirect('listado_pets')
    
    except Exception as e:
        logger.error(f'Error al remover pet: {e}')
        messages.error(request, '❌ Error al remover mascota.')
        return redirect('listado_pets')


# ============================================
# NOTIFICACIONES
# ============================================
@login_required
@role_required(['socio_premium'])
def listado_notificaciones(request):
    """Listado de notificaciones del usuario"""
    try:
        notis = Notificacion.objects.filter(
            usuario_id=request.user,
            is_deleted=False
        ).order_by('-fecha_creacion')
        
        return render(request, 'templatesApp/notificaciones/listado_notificaciones.html', {
            'notificaciones': notis
        })
    
    except Exception as e:
        logger.error(f'Error al listar notificaciones: {e}')
        messages.error(request, '❌ Error al cargar notificaciones.')
        return render(request, 'templatesApp/notificaciones/listado_notificaciones.html', {
            'notificaciones': []
        })


# ============================================
# PANEL DE ADMINISTRACIÓN
# ============================================
@login_required
@user_passes_test(is_admin)
def admin_configuracion(request):
    """Panel de configuración del administrador"""
    return render(request, 'templatesApp/admin/configuracion.html')


# ============================================
# API REST PARA PETS
# ============================================
@api_view(['GET', 'POST'])
@login_required
def pet_list_api(request):
    """API para listar y crear mascotas"""
    if request.method == 'GET':
        try:
            pets = Pet.objects.filter(
                responsable_id=request.user.id_usuario
            ).filter(Q(is_deleted=0) | Q(is_deleted__isnull=True))
            serializer = PetSerializer(pets, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f'Error en API GET pets: {e}')
            return Response(
                {'error': 'Error al obtener mascotas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'POST':
        try:
            nombre_pet = request.data.get('nombre_pet', '').strip()
            descripcion_pet = request.data.get('descripcion_pet', '').strip()
            especie = request.data.get('especie', '').strip()
            sexo = request.data.get('sexo', '').strip()
            tamanio = request.data.get('tamanio', '').strip()
            raza = request.data.get('raza') or None
            es_mestizo = request.data.get('es_mestizo')
            es_mestizo_val = 1 if str(es_mestizo) in ['1', 'true', 'True'] else 0
            peso_kg = request.data.get('peso_kg')
            edad = request.data.get('edad')
            fecha_nacimiento = request.data.get('fecha_nacimiento') or None
            alergias = request.data.get('alergias') or ''
            numero_ficha = request.data.get('numero_ficha')

            if not all([nombre_pet, descripcion_pet, especie, sexo, tamanio]):
                return Response({'error': 'Faltan campos obligatorios'}, status=status.HTTP_400_BAD_REQUEST)

            if not numero_ficha or Pet.objects.filter(numero_ficha=numero_ficha).exists():
                numero_ficha = f'PET-{uuid.uuid4().hex[:8].upper()}'

            # Asegurar raza cuando es mestizo
            if es_mestizo_val == 1 and not raza:
                raza = 'Mestizo'

            # Convertir peso a Decimal si corresponde
            peso_decimal = None
            if peso_kg not in [None, '']:
                try:
                    peso_decimal = Decimal(str(peso_kg).replace(',', '.'))
                except InvalidOperation:
                    return Response({'error': 'Peso inválido'}, status=status.HTTP_400_BAD_REQUEST)

            pet = Pet(
                nombre_pet=nombre_pet,
                descripcion_pet=descripcion_pet,
                especie=especie,
                sexo=sexo,
                tamanio=tamanio,
                raza=raza,
                es_mestizo=es_mestizo_val,
                peso_kg=peso_decimal,
                edad=int(edad) if edad not in [None, ''] else None,
                fecha_nacimiento=fecha_nacimiento,
                alergias=alergias,
                numero_ficha=numero_ficha,
                responsable_id=request.user.id_usuario,
                is_deleted=0
            )
            pet.save()

            if 'foto_url' in request.FILES:
                pet.foto_url = request.FILES['foto_url']
                pet.save()

            logger.info(f'Pet creado via API por usuario {request.user.id_usuario} (id_pet={pet.id_pet})')
            return Response(PetSerializer(pet).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f'Error en API POST pet: {e}')
            return Response(
                {'error': 'Error al crear mascota', 'error_detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET', 'PUT', 'DELETE'])
@login_required
def pet_detail_api(request, pk):
    """API para detalle, actualizar y eliminar mascota"""
    try:
        pet = Pet.objects.filter(pk=pk, responsable_id=request.user.id_usuario).filter(Q(is_deleted=0) | Q(is_deleted__isnull=True)).first()
        if not pet:
            raise Pet.DoesNotExist
    except Pet.DoesNotExist:
        return Response(
            {'error': 'Mascota no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = PetSerializer(pet)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        try:
            serializer = PetSerializer(pet, data=request.data)
            if serializer.is_valid():
                serializer.save(responsable_id=request.user.id_usuario)
                logger.info(f'Pet actualizado via API: {pk}')
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f'Error en API PUT pet: {e}')
            return Response(
                {'error': 'Error al actualizar mascota'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'DELETE':
        try:
            pet.is_deleted = True
            pet.save()
            logger.info(f'Pet eliminado via API: {pk}')
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            logger.error(f'Error en API DELETE pet: {e}')
            return Response(
                {'error': 'Error al eliminar mascota'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# EVENTOS CLÍNICOS
# ============================================
@login_required
@role_required(['socio', 'socio_premium'])
def registrar_evento_clinico(request, pk):
    """Registrar evento clínico con archivos adjuntos"""
    try:
        if is_admin(request.user):
            pet = get_object_or_404(Pet, pk=pk, is_deleted=False)
        else:
            pet = get_object_or_404(Pet, pk=pk, responsable_id=request.user, is_deleted=False)
        
        if request.method == 'POST':
            fecha_evento = request.POST.get('eventDate')
            tipo_evento = request.POST.get('tipoEvento')
            sintomas = request.POST.get('sintomas')
            
            if not all([fecha_evento, tipo_evento, sintomas]):
                messages.error(request, '❌ Todos los campos son obligatorios.')
                return render(request, 'templatesApp/evento/agregar-eventoclinico.html', {'pet': pet})
            
            try:
                with transaction.atomic():
                    # Crear evento clínico
                    evento = EventoClinico.objects.create(
                        id_pet=pet,
                        id_usuario_responsable=request.user,
                        fecha_evento=fecha_evento,
                        tipo_evento=tipo_evento,
                        sintomas_reportados=sintomas,
                        estado_preconsulta='pendiente'
                    )
                    
                    # Procesar fotos (máximo 4)
                    fotos = request.FILES.getlist('fotos')
                    for i, foto in enumerate(fotos[:4]):
                        from django.core.files.storage import default_storage
                        file_name = f'eventos_clinicos/{evento.id_eventoclinico}_{i}_{foto.name}'
                        file_path = default_storage.save(file_name, foto)
                        
                        ArchivoAdjunto.objects.create(
                            id_eventoclinico=evento,
                            archivo_url=file_path,
                            descripcion=f'Foto {i+1} del evento',
                            subido_por=request.user
                        )
                    
                    messages.success(request, '✅ Evento clínico registrado exitosamente.')
                    logger.info(f'Evento clínico creado: {evento.id_eventoclinico}')
                    return redirect('listado_eventos_clinicos', pk=pet.id_pet)
            
            except Exception as e:
                logger.error(f'Error al registrar evento clínico: {e}')
                messages.error(request, '❌ Error al registrar evento.')
        
        return render(request, 'templatesApp/evento/agregar-eventoclinico.html', {'pet': pet})
    
    except Pet.DoesNotExist:
        messages.error(request, '❌ Mascota no encontrada.')
        return redirect('listado_pets')


@login_required
@role_required(['socio', 'socio_premium'])
def listado_eventos_clinicos(request, pk):
    """Listado de eventos clínicos de una mascota"""
    try:
        if is_admin(request.user):
            pet = get_object_or_404(Pet, pk=pk, is_deleted=False)
            eventos = EventoClinico.objects.filter(
                id_pet=pet,
                is_deleted=False
            ).order_by('-fecha_evento', '-fecha_registro')
        else:
            pet = get_object_or_404(Pet, pk=pk, responsable_id=request.user, is_deleted=False)
            eventos = EventoClinico.objects.filter(
                id_pet=pet,
                id_usuario_responsable=request.user,
                is_deleted=False
            ).order_by('-fecha_evento', '-fecha_registro')
        
        # Obtener fotos para cada evento
        eventos_con_fotos = []
        for evento in eventos:
            fotos = ArchivoAdjunto.objects.filter(
                id_eventoclinico=evento,
                is_deleted=False
            )
            eventos_con_fotos.append({
                'evento': evento,
                'fotos': fotos
            })
        
        return render(request, 'templatesApp/evento/listado-eventosclinicos.html', {
            'pet': pet,
            'eventos_con_fotos': eventos_con_fotos
        })
    
    except Pet.DoesNotExist:
        messages.error(request, '❌ Mascota no encontrada.')
        return redirect('listado_pets')
    
    except Exception as e:
        logger.error(f'Error al listar eventos clínicos: {e}')
        messages.error(request, '❌ Error al cargar eventos clínicos.')
        return redirect('detalle_pet', pk=pk)


# ============================================
# API EXTERNA - RAZAS (DOG API / CAT API)
# ============================================
class RazasAPI(View):
    """API para obtener razas de perros y gatos"""
    
    def get(self, request):
        especie = request.GET.get('especie', '').lower()
        
        if especie == 'perro':
            url = 'https://api.thedogapi.com/v1/breeds'
            api_key = settings.DOG_API_KEY
        elif especie == 'gato':
            url = 'https://api.thecatapi.com/v1/breeds'
            api_key = settings.CAT_API_KEY
        else:
            return JsonResponse({'error': 'Especie inválida'}, status=400)
        
        try:
            headers = {'x-api-key': api_key}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            razas = [{'id': r['id'], 'name': r['name']} for r in response.json()]
            logger.info(f'Razas obtenidas para especie: {especie}')
            return JsonResponse({'razas': razas[:50]})
        
        except requests.Timeout:
            logger.error(f'Timeout al obtener razas de {especie}')
            return JsonResponse({'error': 'Tiempo de espera agotado'}, status=504)
        
        except requests.RequestException as e:
            logger.error(f'Error al obtener razas: {e}')
            return JsonResponse({'error': f'API externa falló: {str(e)}'}, status=500)
        
        except Exception as e:
            logger.error(f'Error inesperado en RazasAPI: {e}')
            return JsonResponse({'error': 'Error interno del servidor'}, status=500)
        
        

@login_required
def gestionar_cuidados(request, pk):
    pet = get_object_or_404(Pet, id_pet=pk)
    cuidados = Cuidados.objects.filter(id_pet=pk, is_deleted=0).order_by('-fecha_proxima')
    
    if request.method == 'POST':
        tipo_cuidado = request.POST.get('tipo_cuidado')
        fecha_proxima = request.POST.get('fecha_proxima')
        dosis = request.POST.get('dosis')
        
        Cuidados.objects.create(
            id_pet=pet,
            tipo_cuidado=tipo_cuidado,
            fecha_proxima=fecha_proxima,
            dosis=dosis or None
        )
        messages.success(request, 'Cuidado agregado exitosamente.')
        return redirect('gestionar_cuidados', pk=pk)
    
    return render(request, 'templatesApp/cuidados/gestionar-cuidados.html', {
        'pet': pet,
        'cuidados': cuidados
    })

@login_required
def editar_cuidado(request, pk, cuidado_id):
    pet = get_object_or_404(Pet, id_pet=pk)
    cuidado = get_object_or_404(Cuidados, id_cuidado=cuidado_id, id_pet=pk)
    cuidados = Cuidados.objects.filter(id_pet=pk, is_deleted=0).order_by('-fecha_proxima')
    
    if request.method == 'POST':
        cuidado.tipo_cuidado = request.POST.get('tipo_cuidado')
        cuidado.fecha_proxima = request.POST.get('fecha_proxima')
        cuidado.dosis = request.POST.get('dosis') or None
        cuidado.save()
        messages.success(request, 'Cuidado actualizado exitosamente.')
        return redirect('gestionar_cuidados', pk=pk)
    
    return render(request, 'templatesApp/cuidados/gestionar-cuidados.html', {
        'pet': pet,
        'cuidados': cuidados,
        'cuidado_editar': cuidado
    })

@login_required
def eliminar_cuidado(request, pk, cuidado_id):
    cuidado = get_object_or_404(Cuidados, id_cuidado=cuidado_id, id_pet=pk)
    cuidado.is_deleted = 1
    cuidado.save()
    messages.success(request, 'Cuidado eliminado exitosamente.')
    return redirect('gestionar_cuidados', pk=pk)
