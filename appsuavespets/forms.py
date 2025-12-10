from django import forms
from .models import Usuario, Pet, ArchivoAdjunto, Notificacion, EventoClinico
from django.core.exceptions import ValidationError
import re


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
        if len(nombre) > 50:
            raise ValidationError('El nombre debe tener máximo 50 caracteres.')
        return nombre.title()

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este email ya está registrado.')
        if not re.match(r'^[^\s@]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email or ''):
            raise ValidationError('Formato de email inválido.')
        dominio = email.split('@')[-1]
        edu_suffixes = {
            'edu.ar','edu.cl'
        }
        known_university_suffixes = {
            # Chile (Vet)
            'uchile.cl','uach.cl','unab.cl','umayor.cl','uvm.cl','udec.cl','uss.cl','udla.cl',
            # Argentina (Vet)
            'uba.ar','unlp.edu.ar','unr.edu.ar','unicen.edu.ar','unne.edu.ar','unrc.edu.ar','unl.edu.ar','usal.edu.ar','unimoron.edu.ar'
        }
        proveedores = {
            'gmail.com','outlook.com','hotmail.com','live.com','yahoo.com','icloud.com','protonmail.com','gmx.com','aol.com'
        }
        desechables = {
            'mailinator.com','yopmail.com','tempmail.com','10minutemail.com','guerrillamail.com','discard.email','trashmail.com'
        }
        tlds = {
            'com','net','org','edu','gov','mil','info','biz','io','co','us','uk','es','cl','mx','ar','pe','uy','br','ve','cr','pa','ec','ca','de','fr','it'
        }
        if dominio in desechables:
            raise ValidationError('No se permiten correos de dominios desechables.')
        if any(dominio.endswith(suf) for suf in edu_suffixes | known_university_suffixes):
            return email
        if dominio in proveedores:
            return email
        partes = dominio.split('.')
        if len(partes) < 2:
            raise ValidationError('Dominio de email inválido.')
        sld, tld = partes[-2], partes[-1]
        if len(sld) < 2 or not re.match(r'^[A-Za-z0-9-]+$', sld):
            raise ValidationError('Dominio corporativo inválido.')
        if tld.lower() not in tlds:
            raise ValidationError('Dominio de email no reconocido.')
        if dominio.startswith('-') or dominio.endswith('-') or '..' in dominio:
            raise ValidationError('Dominio de email inválido.')
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

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if not re.match(r'^[^\s@]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email or ''):
            raise ValidationError('Formato de email inválido.')
        dominio = email.split('@')[-1]
        edu_suffixes = {
            'edu.ar','edu.cl'
        }
        known_university_suffixes = {
            'uchile.cl','uach.cl','unab.cl','umayor.cl','uvm.cl','udec.cl','uss.cl','udla.cl',
            'uba.ar','unlp.edu.ar','unr.edu.ar','unicen.edu.ar','unne.edu.ar','unrc.edu.ar','unl.edu.ar','usal.edu.ar','unimoron.edu.ar'
        }
        proveedores = {
            'gmail.com','outlook.com','hotmail.com','live.com','yahoo.com','icloud.com','protonmail.com','gmx.com','aol.com'
        }
        desechables = {
            'mailinator.com','yopmail.com','tempmail.com','10minutemail.com','guerrillamail.com','discard.email','trashmail.com'
        }
        tlds = {
            'com','net','org','edu','gov','mil','info','biz','io','co','us','uk','es','cl','mx','ar','pe','uy','br','ve','cr','pa','ec','ca','de','fr','it'
        }
        if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Este email ya está registrado.')
        if dominio in desechables:
            raise ValidationError('No se permiten correos de dominios desechables.')
        if any(dominio.endswith(suf) for suf in edu_suffixes | known_university_suffixes):
            return email
        if dominio in proveedores:
            return email
        partes = dominio.split('.')
        if len(partes) < 2:
            raise ValidationError('Dominio de email inválido.')
        sld, tld = partes[-2], partes[-1]
        if len(sld) < 2 or not re.match(r'^[A-Za-z0-9-]+$', sld):
            raise ValidationError('Dominio corporativo inválido.')
        if tld.lower() not in tlds:
            raise ValidationError('Dominio de email no reconocido.')
        if dominio.startswith('-') or dominio.endswith('-') or '..' in dominio:
            raise ValidationError('Dominio de email inválido.')
        return email

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

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if Usuario.objects.filter(email=email).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise ValidationError('Este email ya está registrado.')
        if not re.match(r'^[^\s@]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email or ''):
            raise ValidationError('Formato de email inválido.')
        dominio = email.split('@')[-1]
        edu_suffixes = {
            'edu.ar','edu.cl'
        }
        known_university_suffixes = {
            'uchile.cl','uach.cl','unab.cl','umayor.cl','uvm.cl','udec.cl','uss.cl','udla.cl',
            'uba.ar','unlp.edu.ar','unr.edu.ar','unicen.edu.ar','unne.edu.ar','unrc.edu.ar','unl.edu.ar','usal.edu.ar','unimoron.edu.ar'
        }
        proveedores = {
            'gmail.com','outlook.com','hotmail.com','live.com','yahoo.com','icloud.com','protonmail.com','gmx.com','aol.com'
        }
        desechables = {
            'mailinator.com','yopmail.com','tempmail.com','10minutemail.com','guerrillamail.com','discard.email','trashmail.com'
        }
        tlds = {
            'com','net','org','edu','gov','mil','info','biz','io','co','us','uk','es','cl','mx','ar','pe','uy','br','ve','cr','pa','ec','ca','de','fr','it'
        }
        if dominio in desechables:
            raise ValidationError('No se permiten correos de dominios desechables.')
        if any(dominio.endswith(suf) for suf in edu_suffixes | known_university_suffixes):
            return email
        if dominio in proveedores:
            return email
        partes = dominio.split('.')
        if len(partes) < 2:
            raise ValidationError('Dominio de email inválido.')
        sld, tld = partes[-2], partes[-1]
        if len(sld) < 2 or not re.match(r'^[A-Za-z0-9-]+$', sld):
            raise ValidationError('Dominio corporativo inválido.')
        if tld.lower() not in tlds:
            raise ValidationError('Dominio de email no reconocido.')
        if dominio.startswith('-') or dominio.endswith('-') or '..' in dominio:
            raise ValidationError('Dominio de email inválido.')
        return email

class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ['nombre_pet', 'descripcion_pet', 'especie', 'tamanio', 'raza', 'es_mestizo', 'sexo', 'edad', 'fecha_nacimiento', 'peso_kg', 'foto_url']
        widgets = {
            'nombre_pet': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la mascota'}),
            'descripcion_pet': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe temperamento, salud y otros detalles'}),
            'especie': forms.Select(attrs={'class': 'form-select'}),
            'tamanio': forms.Select(attrs={'class': 'form-select'}),
            'raza': forms.TextInput(attrs={'class': 'form-control'}),
            'es_mestizo': forms.HiddenInput(),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'edad': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0, 
                'max': 30,
                'step': '1',
                'placeholder': 'Dejar vacío si es desconocida'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'peso_kg': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': 0.4,
                'max': 160,
                'pattern': r'[0-9]+([.][0-9]+)?',
                'inputmode': 'decimal',
                'placeholder': 'Opcional'
            }),
            'foto_url': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png'}),
            'especie': forms.Select(attrs={'class': 'form-select', 'disabled': 'disabled'}),
        }
        labels = {
            'nombre_pet': 'Nombre',
            'descripcion_pet': 'Descripción',
            'especie': 'Especie',
            'tamanio': 'Tamaño',
            'raza': 'Raza',
            'sexo': 'Sexo',
            'edad': 'Edad (años)',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'peso_kg': 'Peso (kg)',
            'foto_url': 'Foto',
        }

    def clean_peso_kg(self):
        """Validación adicional para peso SOLO si se ingresa"""
        peso = self.cleaned_data.get('peso_kg')
        
        # Si está vacío, está bien (es opcional)
        if peso is None or peso == '':
            return None
        
        if peso < 0.4:
            raise forms.ValidationError('El peso mínimo es 0.4 kg')
        
        if peso > 160:
            raise forms.ValidationError('El peso máximo es 160 kg')
        
        # Validar que tenga máximo 2 decimales
        peso_str = str(peso)
        if '.' in peso_str:
            decimales = len(peso_str.split('.')[1])
            if decimales > 2:
                raise forms.ValidationError('El peso puede tener máximo 2 decimales')
        
        return peso

    def clean(self):
        cleaned = super().clean()
        dob = cleaned.get('fecha_nacimiento')
        edad = cleaned.get('edad')
        from datetime import date
        if dob:
            if dob > date.today():
                self.add_error('fecha_nacimiento', 'La fecha no puede ser futura')
            if edad is not None:
                years = int((date.today() - dob).days // 365)
                if years != int(edad):
                    self.add_error('edad', 'La edad no coincide con la fecha de nacimiento')
        # No permitir modificar especie desde este formulario
        if self.instance and getattr(self.instance, 'especie', None):
            cleaned['especie'] = self.instance.especie
        return cleaned

    def clean_foto_url(self):
        foto = self.cleaned_data.get('foto_url')
        if not foto:
            return foto
        content_type = getattr(foto, 'content_type', '')
        name = getattr(foto, 'name', '')
        allowed_ct = ['image/jpeg', 'image/png']
        allowed_ext = ('.jpg', '.jpeg', '.png')
        if content_type and content_type.lower() not in allowed_ct:
            raise forms.ValidationError('Solo se permiten imágenes JPG o PNG')
        if name and not name.lower().endswith(allowed_ext):
            raise forms.ValidationError('Extensión de archivo no permitida')
        # Validar que realmente es una imagen
        try:
            from PIL import Image
            Image.open(foto).verify()
        except Exception:
            raise forms.ValidationError('Archivo de imagen inválido')
        # Limitar tamaño (5 MB)
        max_bytes = 5 * 1024 * 1024
        if getattr(foto, 'size', 0) > max_bytes:
            raise forms.ValidationError('La imagen supera 5 MB')
        return foto
    
    
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
