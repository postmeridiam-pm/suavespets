"""
URL configuration for suavespets project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from appsuavespets import views
from appsuavespets import auth_views
from appsuavespets import configuration_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('registro/', auth_views.registro_view, name='registro'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('acceso-denegado/', auth_views.acceso_denegado, name='acceso_denegado'),

    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    path('configuracion/', configuration_views.admin_configuracion, name='panel_configuracion'),  # Solo admin
    path('configuracion/cambiar-contrasena/', configuration_views.cambiar_contrasena, name='cambiar_contrasena'),
    path('configuracion/preferencias/', configuration_views.preferencias, name='preferencias'),
    path('configuracion/usuarios/', configuration_views.gestionar_usuarios, name='gestionar_usuarios'),
    path('configuracion/usuarios/asignar/<int:user_id>/', configuration_views.asignar_rol, name='asignar_rol'),
    path('configuracion/usuarios/crear/', configuration_views.crear_usuario_especial, name='crear_usuario_especial'),

    path('pets/', views.listado_pets, name='listado_pets'),
    path('pets/nueva/', views.agregar_pet, name='agregar_pet'),
    path('pets/<int:pk>/', views.detalle_pet, name='detalle_pet'),
    path('pets/<int:pk>/actualizar/', views.actualizar_pet, name='actualizar_pet'),
    path('pets/<int:pk>/remover/', views.remover_pet, name='remover_pet'),
    
    path('pets/<int:pk>/evento-clinico/', views.registrar_evento_clinico, name='registrar_evento_clinico'),
    path('pets/<int:pk>/eventos/', views.listado_eventos_clinicos, name='listado_eventos_clinicos'),

    path('api/pets/', views.pet_list_api, name='api_pet_list'),
    path('api/pets/<int:pk>/', views.pet_detail_api, name='api_pet_detail'),

    path('notificaciones/', views.listado_notificaciones, name='listado_notificaciones'),

    path('', views.inicio, name='inicio'),
    path('api/razas/', views.RazasAPI.as_view(), name='razas_api'),
    
    path('pets/<int:pk>/cuidados/', views.gestionar_cuidados, name='gestionar_cuidados'),
    path('pets/<int:pk>/cuidados/<int:cuidado_id>/editar/', views.editar_cuidado, name='editar_cuidado'),
    path('pets/<int:pk>/cuidados/<int:cuidado_id>/eliminar/', views.eliminar_cuidado, name='eliminar_cuidado'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    
    
