# core/urls.py
from django.urls import path, include
from django.contrib import admin
from . import views
from .views import CrearOrdenView

#app_name = 'core'  # Para poder usar namespace en reversas

urlpatterns = [
    # ==================== DJANGO ADMIN OFICIAL ====================
    # Admin de Django (solo para superusuarios) movido a /django-admin/
    path('django-admin/', admin.site.urls),

    # ==================== RUTAS PÚBLICAS (sin prefijo) ====================
    path('', views.home, name='home'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('carrito/', views.carrito, name='carrito'),
    path('mis-compras/', views.mis_compras, name='mis_compras'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('checkout/', views.checkout, name='checkout'),
    path('orden-exitosa/<int:orden_id>/', views.orden_exitosa, name='orden_exitosa'),

    # Carrito y acciones
    path('add_to_carrito/<int:producto_id>/', views.add_to_carrito, name='add_to_carrito'),
    path('remove_from_carrito/<int:item_id>/', views.remove_from_carrito, name='remove_from_carrito'),
    path('carrito/actualizar/<int:item_id>/', views.actualizar_cantidad_carrito, name='actualizar_cantidad_carrito'),

    # Autenticación y verificación
    path('verificar-codigo/', views.verificar_codigo, name='verificar_codigo'),
    path('reenviar-codigo/', views.reenviar_codigo, name='reenviar_codigo'),
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('cambiar-password/<str:token>/', views.cambiar_password_view, name='cambiar_password'),
    path('cambiar-correo-registro/', views.cambiar_correo_registro, name='cambiar_correo_registro'),

    # Escaneo rápido (con posibilidad de edición)
    path('escaneo/', views.escaneo_rapido, name='escaneo_rapido'),
    path('escaneo/editar/<int:pk>/', views.escaneo_rapido, name='editar_precio_rapido'),

    # API y utilidades
    path('api/productos/', views.ProductoListAPIView.as_view(), name='producto_list_api'),
    path('crear-orden/', CrearOrdenView.as_view(), name='crear_orden'),
    path('test-correo/', views.test_correo),  # Solo desarrollo, quitar en producción
    path('test-endpoint/', views.test_endpoint_view, name='test_endpoint'),

    # ==================== PANEL DE GESTIÓN (para administradores y gestores) ====================
    # Panel principal
    path('panel/', views.admin_panel, name='admin_panel'),
    path('panel/home/', views.admin_home, name='admin_home'),

    # Gestión de productos (solo para administradores de productos)
    path('panel/productos/', views.producto_list, name='producto_list'),
    path('panel/producto/crear/', views.producto_create, name='producto_create'),
    path('panel/producto/editar/<int:producto_id>/', views.producto_update, name='producto_update'),
    path('panel/producto/eliminar/<int:producto_id>/', views.producto_delete, name='producto_delete'),
    path('panel/producto/crear-con-codigo/', views.redirigir_crear_producto_con_codigo, name='crear_producto_con_codigo'),

    path('todos-los-pedidos/', views.todos_los_pedidos, name='todos_los_pedidos'),
    # Gestión de pedidos y órdenes (para gestores de pedidos)
    # ====================== URL PARA ELIMINAR ÓRDENES ======================
    path('panel/eliminar-orden/', views.eliminar_orden_manual, name='eliminar_orden_manual'),
    path('panel/pedidos/', views.gestion_estados, name='gestion_estados'),
    path('panel/orden/<int:pk>/', views.orden_detail, name='orden_detail'),
    path('panel/cambiar-estado/<int:pk>/', views.cambiar_estado_pedido, name='cambiar_estado_pedido'),
    path('panel/orden/<int:orden_id>/actualizar/', views.update_orden_status, name='update_orden_status'),
    path('panel/pedidos-despacho/', views.pedidos_despacho, name='pedidos_despacho'),
    path('panel/pedidos-finalizados/', views.pedidos_finalizados, name='pedidos_finalizados'),
    # Gestión de banners (posiblemente solo administrador total)
    path('panel/banners/', views.gestion_banners, name='gestion_banners'),
    path('escaneo-rapido-pedidos/', views.escaneo_rapido_pedidos, name='escaneo_rapido_pedidos'),
    path('api/agregar-por-codigo/', views.agregar_por_codigo_api, name='agregar_por_codigo_api'),
    path('api/limpiar-carrito/', views.limpiar_carrito_api, name='limpiar_carrito_api'),
]
