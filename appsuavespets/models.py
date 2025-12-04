# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = True` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class ArchivoAdjunto(models.Model):
    id_archivo = models.AutoField(primary_key=True)
    id_eventoclinico = models.ForeignKey('EventoClinico', models.DO_NOTHING, blank=True, null=True)
    archivo_url = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    fecha_subida = models.DateTimeField()
    subido_por = models.ForeignKey('Usuario', models.DO_NOTHING, blank=True, null=True)
    is_deleted = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'archivo_adjunto'


class Auditoria(models.Model):
    id_auditoria = models.BigAutoField(primary_key=True)
    tabla_afectada = models.CharField(max_length=50)
    operacion = models.CharField(max_length=6)
    registro_id = models.IntegerField()
    usuario = models.ForeignKey('Usuario', models.DO_NOTHING, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    ip_origen = models.CharField(max_length=45, blank=True, null=True)
    fecha_operacion = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'auditoria'


class Cuidados(models.Model):
    id_cuidado = models.AutoField(primary_key=True)
    id_pet = models.ForeignKey('Pet', models.DO_NOTHING, db_column='id_pet')
    tipo_cuidado = models.CharField(max_length=50)
    fecha_proxima = models.DateField()
    dosis = models.CharField(max_length=120, blank=True, null=True)
    is_deleted = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'cuidados'



class EventoClinico(models.Model):
    id_eventoclinico = models.AutoField(primary_key=True)
    id_pet = models.ForeignKey('Pet', models.DO_NOTHING, db_column='id_pet')
    id_usuario_responsable = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario_responsable')
    fecha_evento = models.DateField()
    tipo_evento = models.CharField(max_length=20)
    sintomas_reportados = models.TextField()
    descripcion_evento = models.TextField(blank=True, null=True)
    estado_preconsulta = models.CharField(max_length=30, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(blank=True, null=True)
    is_deleted = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'evento_clinico'


class Notificacion(models.Model):
    id_notificacion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey('Usuario', models.DO_NOTHING)
    pet = models.ForeignKey('Pet', on_delete=models.DO_NOTHING, blank=True, null=True)
    titulo = models.CharField(max_length=100, blank=True, null=True)
    mensaje = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=20, blank=True, null=True)
    leido = models.IntegerField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    is_deleted = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'notificacion'


class Pet(models.Model):
    ESPECIE_CHOICES = [
        ('perro', 'Perro'),
        ('gato', 'Gato'),
    ]
    
    SEXO_CHOICES = [
        ('macho', 'Macho'),
        ('hembra', 'Hembra'),
    ]
    
    TAMANIO_CHOICES = [
        ('pequeno', 'Pequeño'),
        ('mediano', 'Mediano'),
        ('grande', 'Grande'),
        ('gigante', 'Gigante'),
    ]
    
    id_pet = models.AutoField(primary_key=True)
    nombre_pet = models.CharField(max_length=100)
    descripcion_pet = models.TextField(blank=True)
    especie = models.CharField(max_length=10, choices=ESPECIE_CHOICES)
    tamanio = models.CharField(max_length=10, choices=TAMANIO_CHOICES)
    raza = models.CharField(max_length=100)
    es_mestizo = models.BooleanField(default=False)
    sexo = models.CharField(max_length=10, choices=SEXO_CHOICES, blank=True, null=True) 
    edad = models.IntegerField(blank=True, null=True) 
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    numero_ficha = models.CharField(max_length=50, unique=True, blank=True, null=True)
    alergias = models.TextField(blank=True, null=True)
    responsable = models.ForeignKey('Usuario', models.DO_NOTHING, blank=True, null=True)
    veterinario = models.ForeignKey('Usuario', models.DO_NOTHING, blank=True, null=True, related_name='pet_veterinario_set')
    is_deleted = models.IntegerField(blank=True, null=True, default=0)
    foto_url = models.ImageField(upload_to='pets/', blank=True, null=True)
    foto = models.URLField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'pet'

class ProductoVeterinario(models.Model):
    id_producto = models.AutoField(primary_key=True)
    tipo_producto = models.CharField(max_length=11)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    laboratorio = models.CharField(max_length=100, blank=True, null=True)
    requiere_receta = models.IntegerField()
    is_deleted = models.IntegerField()
    fecha_creacion = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'producto_veterinario'



class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    id_usuario = models.AutoField(primary_key=True, db_column='id_usuario')  # ← AGREGAR
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    tipo_identificacion = models.CharField(max_length=20)
    identificacion = models.CharField(max_length=20)
    dni = models.CharField(max_length=20, blank=True, null=True)  # ← AGREGAR si existe en tu tabla
    telefono = models.CharField(max_length=15, blank=True, null=True)
    tipo_usuario = models.CharField(max_length=20, default='invitado')
    cuota_activa = models.BooleanField(default=False)
    fecha_vencimiento_cuota = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Si tu columna se llama 'hash_contrasenia' en vez de 'password':
    password = models.CharField(max_length=128, db_column='hash_contrasenia')  # ← AGREGAR
    
    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'tipo_identificacion', 'identificacion']

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'usuario' 
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
