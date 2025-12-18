from django.contrib import admin
from .models import Alumno, Materia, Calificacion

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre']
    search_fields = ['codigo', 'nombre']
    ordering = ['codigo']

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = [
        'matricula', 
        'nombre_completo',
        'semestre', 
        'grupo', 
        'sexo',
        'prom_1er_parcial_general_display',
        'prom_2do_parcial_general_display',
        'prom_3er_parcial_general_display',
        'prom_final_general_display',
        'activo'
    ]
    
    list_filter = ['semestre', 'grupo', 'sexo', 'activo', 'carrera']
    search_fields = ['matricula', 'primer_nombre', 'primer_apellido', 'segundo_apellido']
    ordering = ['matricula']
    readonly_fields = ['fecha_registro']
    
    # Solo el campo 'activo' es editable en la lista
    list_editable = ['activo']
    
    # Métodos para mostrar promedios en la lista
    def prom_1er_parcial_general_display(self, obj):
        promedio = obj.prom_1er_parcial_general
        if promedio is not None:
            return f"{promedio:.1f}"
        return "-"
    prom_1er_parcial_general_display.short_description = "1er Parcial"
    
    def prom_2do_parcial_general_display(self, obj):
        promedio = obj.prom_2do_parcial_general
        if promedio is not None:
            return f"{promedio:.1f}"
        return "-"
    prom_2do_parcial_general_display.short_description = "2do Parcial"
    
    def prom_3er_parcial_general_display(self, obj):
        promedio = obj.prom_3er_parcial_general
        if promedio is not None:
            return f"{promedio:.1f}"
        return "-"
    prom_3er_parcial_general_display.short_description = "3er Parcial"
    
    def prom_final_general_display(self, obj):
        promedio = obj.prom_final_general
        if promedio is not None:
            return f"{promedio:.1f}"
        return "-"
    prom_final_general_display.short_description = "Final"
    
    # Campos en el formulario de edición
    fieldsets = (
        ('Información Personal', {
            'fields': (
                'matricula',
                ('primer_nombre', 'segundo_nombre'),
                ('primer_apellido', 'segundo_apellido'),
                ('semestre', 'grupo', 'sexo', 'carrera'),
            )
        }),
        ('Datos del Sistema', {
            'fields': ('activo', 'fecha_registro'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    # Usar los nombres reales de los campos para que list_editable funcione
    list_display = [
        'alumno_matricula',
        'materia_codigo',
        'p1',  # Nombre real del campo
        'p2',  # Nombre real del campo
        'p3',  # Nombre real del campo
        'promedio_parciales_display',
        'examen_final',  # Nombre real del campo
        'calificacion_final_display',
        'estado'
    ]
    
    list_filter = ['materia', 'alumno__semestre', 'alumno__grupo']
    search_fields = ['alumno__matricula', 'alumno__primer_apellido', 'materia__codigo']
    ordering = ['alumno__matricula', 'materia__codigo']
    
    # Ahora estos campos SÍ están en list_display
    list_editable = ['p1', 'p2', 'p3', 'examen_final']
    
    # Métodos para mostrar en la lista
    def alumno_matricula(self, obj):
        return obj.alumno.matricula
    alumno_matricula.short_description = "Matrícula"
    alumno_matricula.admin_order_field = 'alumno__matricula'
    
    def materia_codigo(self, obj):
        return obj.materia.codigo
    materia_codigo.short_description = "Materia"
    materia_codigo.admin_order_field = 'materia__codigo'
    
    def promedio_parciales_display(self, obj):
        return obj.promedio_parciales if obj.promedio_parciales is not None else "-"
    promedio_parciales_display.short_description = "Prom. Parciales"
    
    def calificacion_final_display(self, obj):
        return obj.calificacion_final if obj.calificacion_final is not None else "-"
    calificacion_final_display.short_description = "Calif. Final"
    
    # Campos en el formulario de edición
    fieldsets = (
        ('Información General', {
            'fields': ('alumno', 'materia')
        }),
        ('Calificaciones', {
            'fields': (
                ('p1', 'p2', 'p3'),
                'examen_final'
            )
        }),
        ('Resultados Calculados', {
            'fields': ('promedio_parciales', 'calificacion_final', 'estado'),
            'classes': ('collapse',),
            'description': 'Estos campos se calculan automáticamente al guardar.'
        }),
        ('Fechas', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['promedio_parciales', 'calificacion_final', 'estado', 'fecha_registro', 'fecha_actualizacion']
    
    # Personalizar cómo se muestran los campos en la lista (opcional)
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # Personalizar el widget para los campos de calificación
        from django.forms import NumberInput
        if db_field.name in ['p1', 'p2', 'p3', 'examen_final']:
            kwargs['widget'] = NumberInput(attrs={'min': '0', 'max': '10', 'step': '0.1'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)