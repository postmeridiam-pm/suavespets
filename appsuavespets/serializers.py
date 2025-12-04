from rest_framework import serializers
from .models import Usuario, Pet, ArchivoAdjunto, Notificacion, EventoClinico


# ------------ Pet ------------ 
class PetSerializer(serializers.ModelSerializer):
    responsable_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Pet
        fields = '__all__'

    def get_responsable_data(self, obj):
        usuario = obj.responsable
        if usuario:
            from .serializers import UsuarioSerializer
            return UsuarioSerializer(usuario).data
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('peso_kg') in (None, ''):
            data['peso_kg'] = 'Desconocido'
        if data.get('fecha_nacimiento') in (None, ''):
            data['fecha_nacimiento'] = 'Desconocida'
        return data


# ------------ Usuario ------------
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'


class ArchivoAdjuntoSerializer(serializers.ModelSerializer):
    subido_por = UsuarioSerializer(read_only=True)
    id_eventoclinico = serializers.PrimaryKeyRelatedField(queryset=EventoClinico.objects.all())

    class Meta:
        model = ArchivoAdjunto
        fields = '__all__'


# ------------ EventoClinico ------------
class EventoClinicoSerializer(serializers.ModelSerializer):
    id_pet = PetSerializer(read_only=True)
    id_usuario_responsable = UsuarioSerializer(read_only=True)

    class Meta:
        model = EventoClinico
        fields = '__all__'


# ------------ Notificacion ------------
class NotificacionSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    pet = PetSerializer(read_only=True)

    class Meta:
        model = Notificacion
        fields = '__all__'
