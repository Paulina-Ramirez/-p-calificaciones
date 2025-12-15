from django.contrib import admin
from .models import Alumno

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    # Mostrar en lista (todos en escala 1-10)
    list_display = ['matricula', 'nombre', 'promedio_parciales', 'promedio_profesor', 'promedio_final', 'estado']
    
    # Buscar
    search_fields = ['matricula', 'nombre']
    
    # Campos editables
    fields = ['matricula', 'nombre', 'calificaciones_texto', 'promedio_profesor']
    
    # Solo lectura
    readonly_fields = ['promedio_parciales', 'promedio_final', 'estado', 'fecha_registro']
    
    # Ordenar
    ordering = ['matricula']
    
    # Texto de ayuda actualizado para escala 1-10
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['calificaciones_texto'].help_text = (
            'Formato: Materia:Parcial1:Parcial2:Parcial3, ...<br>'
            'Ejemplo: Matemáticas:8.5:9.0:8.8, Español:9.0:8.5:9.2<br>'
            '<strong>Nota:</strong> Use escala del 1 al 10 (0 si no hay calificación)'
        )
        form.base_fields['promedio_profesor'].help_text = (
            'Promedio adicional que el profesor asigna al alumno<br>'
            '<strong>Escala:</strong> 1 al 10<br>'
            '<strong>Fórmula final:</strong> (Promedio parciales + Este promedio) ÷ 2'
        )
        return form