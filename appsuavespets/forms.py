from django import forms
from .models import Usuario, Pet, ArchivoAdjunto, Notificacion, EventoClinico
from django.core.exceptions import ValidationError
import re

import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Usuario


class RegistroForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Contraseña',
        min_length=8,
        help_text='Mínimo 8 caracteres, incluye letras y números'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirmar contraseña'
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'tipo_identificacion', 'identificacion', 'email', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_identificacion': forms.Select(attrs={'class': 'form-select'}),
            'identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
            raise ValidationError('El nombre solo puede contener letras y espacios.')
        if len(nombre) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres.')
        return nombre.title()

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        
        # Verificar si ya existe
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este email ya está registrado.')
        
        # Validar dominios permitidos
        dominios_permitidos = [
            'gmail.com', 'outlook.com', 'hotmail.com', 'live.com',
            'yahoo.com', 'icloud.com', 'protonmail.com'
        ]
        
        dominio = email.split('@')[-1].lower()
        
        # Permitir dominios conocidos O cualquier dominio corporativo
        if dominio not in dominios_permitidos:
            # Es un dominio corporativo - permitirlo
            # Puedes agregar validación adicional aquí si quieres
            pass
        
        return email

    def es_dominio_corporativo(self, dominio):
        """
        Verifica si es un dominio corporativo (no gratuito)
        Actualmente solo excluye los dominios gratuitos más comunes
        """
        gratuitos = ['gmail.com', 'outlook.com', 'hotmail.com', 'live.com', 'yahoo.com', 'icloud.com']
        return dominio not in gratuitos

    def clean_identificacion(self):
        identificacion = self.cleaned_data.get('identificacion', '').strip()
        tipo_id = self.cleaned_data.get('tipo_identificacion')
        if Usuario.objects.filter(tipo_identificacion=tipo_id, identificacion=identificacion).exists():
            raise ValidationError('Esta identificación ya está registrada.')
        return identificacion

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError('La contraseña debe incluir letras.')
        if not re.search(r'\d', password):
            raise ValidationError('La contraseña debe incluir números.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError({'password_confirm': 'Las contraseñas no coinciden.'})
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.tipo_usuario = 'socio'
        if commit:
            user.save()
        return user


class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'email', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'tipo_identificacion', 'identificacion', 'email', 'telefono', 'tipo_usuario', 'cuota_activa', 'fecha_vencimiento_cuota']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_identificacion': forms.Select(attrs={'class': 'form-select'}),
            'identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_usuario': forms.Select(attrs={'class': 'form-select'}),
            'cuota_activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fecha_vencimiento_cuota': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ['nombre_pet', 'descripcion_pet', 'especie', 'tamanio', 'raza', 'es_mestizo', 'sexo', 'edad', 'peso_kg', 'foto_url']
        widgets = {
            'nombre_pet': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la mascota'}),
            'descripcion_pet': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe temperamento, salud y otros detalles'}),
            'especie': forms.Select(attrs={'class': 'form-select'}),
            'tamanio': forms.Select(attrs={'class': 'form-select'}),
            'raza': forms.TextInput(attrs={'class': 'form-control'}),
            'es_mestizo': forms.HiddenInput(),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'edad': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 30}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0.1}),
            'foto_url': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    # Métodos clean para validaciones específicas

class PetUpdateForm(PetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

class ArchivoAdjuntoForm(forms.ModelForm):
    class Meta:
        model = ArchivoAdjunto
        fields = ['id_eventoclinico', 'archivo_url', 'descripcion', 'subido_por']
        widgets = {
            'id_eventoclinico': forms.Select(attrs={'class': 'form-select'}),
            'archivo_url': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'subido_por': forms.Select(attrs={'class': 'form-select'}),
        }

class NotificacionForm(forms.ModelForm):
    class Meta:
        model = Notificacion
        fields = ['usuario', 'pet', 'titulo', 'mensaje', 'tipo', 'leido', 'fecha_envio']
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-select'}),
            'pet': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo': forms.TextInput(attrs={'class': 'form-control'}),
            'leido': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fecha_envio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class EventoClinicoForm(forms.ModelForm):
    class Meta:
        model = EventoClinico
        fields = ['id_pet', 'id_usuario_responsable', 'fecha_evento', 'tipo_evento', 'sintomas_reportados', 'descripcion_evento', 'estado_preconsulta', 'observaciones']
        widgets = {
            'id_pet': forms.Select(attrs={'class': 'form-select'}),
            'id_usuario_responsable': forms.Select(attrs={'class': 'form-select'}),
            'fecha_evento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo_evento': forms.TextInput(attrs={'class': 'form-control'}),
            'sintomas_reportados': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe los síntomas observados'}),
            'descripcion_evento': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción detallada del evento'}),
            'estado_preconsulta': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '30', 'placeholder': 'Estado de la preconsulta'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observaciones adicionales'}),
        }
