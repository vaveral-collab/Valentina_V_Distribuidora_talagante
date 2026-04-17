from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin oficial - Cambiamos la ruta para evitar conflicto con namespace 'admin'
    #path('admin/', admin.site.urls),

    # Rutas públicas del sitio (home, catálogo, carrito, login, etc.)
    path('', include('core.urls')),
]

# Solo en desarrollo: servir archivos media
if settings.DEBUG:
 urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
