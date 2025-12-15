from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Panel de administración (para el maestro)
    path('admin/', admin.site.urls),
    
    # URLs de la app alumnos (para los estudiantes)
    path('', include('alumnos.urls')),
]

# Solo en desarrollo: servir archivos estáticos
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)