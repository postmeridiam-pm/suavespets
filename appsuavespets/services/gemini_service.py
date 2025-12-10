# services/gemini_service.py
import google.generativeai as genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class GeminiVetService:
    """Servicio para obtener información veterinaria con Gemini"""

    @staticmethod
    def get_pet_health_info(pet):
        """
        Obtiene información de salud personalizada según la raza
        """
        try:
            # Configurar clave API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Seleccionar modelo Gemini
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Preparar contexto según si es mestizo o no
            if pet.es_mestizo:
                contexto_raza = f"""
                IMPORTANTE: Este {pet.especie} es MESTIZO (mezcla de razas).
                
                Los perros y gatos mestizos generalmente presentan:
                - **Vigor híbrido**: Mayor resistencia genética a enfermedades hereditarias
                - Menos problemas congénitos que razas puras
                - Mayor diversidad genética = mejor salud general
                - Menor predisposición a enfermedades específicas de raza
                
                Enfócate en cuidados generales para {pet.especie}s mestizos y menciona el vigor híbrido.
                """
            else:
                contexto_raza = f"""
                Este {pet.especie} es de raza: {pet.raza}
                
                Proporciona información ESPECÍFICA para la raza {pet.raza}, incluyendo:
                - Enfermedades hereditarias y predisposiciones específicas de esta raza
                - Problemas de salud comunes en {pet.raza}
                - Cuidados especiales que requiere esta raza en particular
                """
            
            prompt = f"""
            Eres un veterinario enfocado en prevención y educación. Proporciona información clara y comprensible para personas sin formación veterinaria. Evita lenguaje alarmista (no uses expresiones como "alta mortalidad" o "letal") y prioriza consejos prácticos y señales de alerta comunes. Proporciona información de salud para:
            
            {contexto_raza}
            
            **Datos adicionales:**
            - Especie: {pet.especie}
            - Tamaño: {pet.tamanio}
            - Edad: {pet.edad if pet.edad else 'No especificada'}
            - Sexo: {pet.sexo}
            
            Proporciona la siguiente información en formato de lista simple con viñetas (-), con tono preventivo y amigable:
            
            1. **ENFERMEDADES COMUNES** (5-7 enfermedades específicas)
            2. **ALIMENTOS PROHIBIDOS** (lista de alimentos tóxicos)
            3. **CUIDADOS PREVENTIVOS** (vacunas, desparasitación, higiene)
            4. **ESTUDIOS RECOMENDADOS** (chequeos y exámenes según edad; prioriza evidencia desde 2005 en adelante)
            5. **REFERENCIAS BIBLIOGRÁFICAS** (3-4 referencias de revistas veterinarias del 2005 en adelante)
            
            **FORMATO DE RESPUESTA (usa exactamente este formato):**
            
            ENFERMEDADES:
            - Enfermedad 1: breve descripción
            - Enfermedad 2: breve descripción
            (etc.)
            
            ALIMENTOS_PROHIBIDOS:
            - Alimento 1: razón
            - Alimento 2: razón
            (etc.)
            
            CUIDADOS:
            - Cuidado 1: descripción
            - Cuidado 2: descripción
            (etc.)
            
            ESTUDIOS:
            - Estudio 1: cuándo y por qué
            - Estudio 2: cuándo y por qué
            (etc.)
            
            REFERENCIAS:
            - Autor(es). (Año). Título. Revista.
            - Autor(es). (Año). Título. Revista.
            (etc.)
            
            Usa lenguaje profesional pero comprensible. Sé específico y práctico. Evita generar alarma innecesaria y destaca medidas de prevención y cuándo consultar al veterinario.
            """
            
            # Generar contenido con Gemini
            response = model.generate_content(prompt)
            texto = response.text
            
            # Parsear respuesta para extraer secciones
            info = {
                'enfermedades': '',
                'alimentos_prohibidos': '',
                'cuidados': '',
                'estudios': '',
                'referencias': ''
            }
            
            if 'ENFERMEDADES:' in texto:
                start = texto.find('ENFERMEDADES:') + len('ENFERMEDADES:')
                end = texto.find('ALIMENTOS_PROHIBIDOS:')
                info['enfermedades'] = texto[start:end].strip()
            
            if 'ALIMENTOS_PROHIBIDOS:' in texto:
                start = texto.find('ALIMENTOS_PROHIBIDOS:') + len('ALIMENTOS_PROHIBIDOS:')
                end = texto.find('CUIDADOS:')
                info['alimentos_prohibidos'] = texto[start:end].strip()
            
            if 'CUIDADOS:' in texto:
                start = texto.find('CUIDADOS:') + len('CUIDADOS:')
                end = texto.find('ESTUDIOS:')
                info['cuidados'] = texto[start:end].strip()
            
            if 'ESTUDIOS:' in texto:
                start = texto.find('ESTUDIOS:') + len('ESTUDIOS:')
                end = texto.find('REFERENCIAS:')
                info['estudios'] = texto[start:end].strip()
            
            if 'REFERENCIAS:' in texto:
                start = texto.find('REFERENCIAS:') + len('REFERENCIAS:')
                info['referencias'] = texto[start:].strip()
            
            logger.info('Gemini OK: contenido generado para pet %s (%s)', pet.id_pet, pet.raza)
            return info
        
        except Exception as e:
            logger.error(f'Error en Gemini: {e}')
            return None
