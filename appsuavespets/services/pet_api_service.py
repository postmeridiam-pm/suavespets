import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class PetAPIService:
    """Servicio para obtener información de APIs de mascotas"""
    
    DOG_API_URL = "https://api.thedogapi.com/v1"
    CAT_API_URL = "https://api.thecatapi.com/v1"
    
    @staticmethod
    def get_dog_breeds():
        """Obtiene lista de razas de perros (con cache de 24h)"""
        cached = cache.get('dog_breeds')
        if cached:
            return cached
        
        try:
            headers = {'x-api-key': settings.DOG_API_KEY}
            response = requests.get(
                f"{PetAPIService.DOG_API_URL}/breeds",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                breeds = response.json()
                cache.set('dog_breeds', breeds, 60*60*24)  # Cache 24h
                return breeds
        except Exception as e:
            logger.error(f"Error obteniendo razas de perros: {e}")
        
        return []
    
    @staticmethod
    def get_cat_breeds():
        """Obtiene lista de razas de gatos (con cache de 24h)"""
        cached = cache.get('cat_breeds')
        if cached:
            return cached
        
        try:
            headers = {'x-api-key': settings.CAT_API_KEY}
            response = requests.get(
                f"{PetAPIService.CAT_API_URL}/breeds",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                breeds = response.json()
                cache.set('cat_breeds', breeds, 60*60*24)  # Cache 24h
                return breeds
        except Exception as e:
            logger.error(f"Error obteniendo razas de gatos: {e}")
        
        return []
    
    @staticmethod
    def get_breed_info(especie, raza_nombre):
        """Obtiene información detallada de una raza específica"""
        if not raza_nombre or raza_nombre.lower() == 'mestizo':
            return None
        
        if especie.lower() == 'perro':
            breeds = PetAPIService.get_dog_breeds()
        elif especie.lower() == 'gato':
            breeds = PetAPIService.get_cat_breeds()
        else:
            return None
        
        # Buscar raza específica (case insensitive)
        for breed in breeds:
            if breed['name'].lower() == raza_nombre.lower():
                return {
                    'nombre': breed.get('name', ''),
                    'temperamento': breed.get('temperament', 'No disponible'),
                    'origen': breed.get('origin', 'No disponible'),
                    'descripcion': breed.get('description', 'No disponible'),
                    'peso': breed.get('weight', {}).get('metric', 'No disponible'),
                    'esperanza_vida': breed.get('life_span', 'No disponible'),
                    'imagen': breed.get('image', {}).get('url', '') if 'image' in breed else '',
                    'grupo': breed.get('breed_group', 'No disponible') if especie.lower() == 'perro' else None,
                }
        return None
    
    @staticmethod
    def get_random_image(especie):
        """Obtiene una imagen aleatoria según la especie"""
        try:
            if especie.lower() == 'perro':
                headers = {'x-api-key': settings.DOG_API_KEY}
                response = requests.get(
                    f"{PetAPIService.DOG_API_URL}/images/search",
                    headers=headers,
                    timeout=10
                )
            elif especie.lower() == 'gato':
                headers = {'x-api-key': settings.CAT_API_KEY}
                response = requests.get(
                    f"{PetAPIService.CAT_API_URL}/images/search",
                    headers=headers,
                    timeout=10
                )
            else:
                return None
            
            if response.status_code == 200:
                data = response.json()
                return data[0]['url'] if data else None
        except Exception as e:
            logger.error(f"Error obteniendo imagen aleatoria: {e}")
        
        return None