# alumnos/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Alumno, Materia, Calificacion
from django import forms

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = '__all__'
    
    def clean_prom_primer_parcial(self):
        data = self.cleaned_data.get('prom_primer_parcial')
        if data is not None and (data < 0 or data > 100):
            raise forms.ValidationError("El promedio debe estar entre 0 y 100")
        return data
    
    def clean_prom_segundo_parcial(self):
        data = self.cleaned_data.get('prom_segundo_parcial')
        if data is not None and (data < 0 or data > 100):
            raise forms.ValidationError("El promedio debe estar entre 0 y 100")
        return data
    
    def clean_prom_tercer_parcial(self):
        data = self.cleaned_data.get('prom_tercer_parcial')
        if data is not None and (data < 0 or data > 100):
            raise forms.ValidationError("El promedio debe estar entre 0 y 100")
        return data
    
    def clean_examen_final(self):
        data = self.cleaned_data.get('examen_final')
        if data is not None and (data < 0 or data > 100):
            raise forms.ValidationError("El examen final debe estar entre 0 y 100")
        return data
    
    def clean(self):
        cleaned_data = super().clean()
        # Calcular automáticamente el promedio final
        prom_primer = cleaned_data.get('prom_primer_parcial')
        prom_segundo = cleaned_data.get('prom_segundo_parcial')
        prom_tercer = cleaned_data.get('prom_tercer_parcial')
        examen = cleaned_data.get('examen_final')
        
        if all(val is not None for val in [prom_primer, prom_segundo, prom_tercer, examen]):
            prom_parciales = (float(prom_primer) + float(prom_segundo) + float(prom_tercer)) / 3
            prom_final = (prom_parciales + float(examen)) / 2
            cleaned_data['prom_final_calculado'] = round(prom_final, 1)
        
        return cleaned_data

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    form = AlumnoForm
    
    # Los campos editables DEBEN estar también en list_display
    list_editable = [
        'prom_primer_parcial', 
        'prom_segundo_parcial', 
        'prom_tercer_parcial', 
        'examen_final',
        'activo'
    ]
    
    # Usar los campos reales para que coincidan con list_editable
    list_display = (
        'matricula', 
        'nombre_completo', 
        'semestre', 
        'grupo', 
        'sexo',
        'prom_primer_parcial',    # Campo real - EDITABLE
        'prom_segundo_parcial',   # Campo real - EDITABLE
        'prom_tercer_parcial',    # Campo real - EDITABLE
        'examen_final',           # Campo real - EDITABLE
        'prom_final_calculado',   # Campo real - NO EDITABLE (se calcula)
        'activo',                 # Campo real - EDITABLE
        'fecha_registro'
    )
    
    # Campos de búsqueda
    search_fields = [
        'matricula', 
        'primer_nombre', 
        'primer_apellido',
        'semestre', 
        'grupo'
    ]
    
    # Filtros
    list_filter = [
        'semestre',
        'grupo',
        'sexo',
        'activo',
        'fecha_registro'
    ]
    
    # Campos en el formulario de edición
    fieldsets = (
        ('Información Personal', {
            'fields': (
                'matricula',
                'primer_apellido',
                'segundo_apellido',
                'primer_nombre',
                'segundo_nombre',
                'semestre',
                'grupo',
                'sexo'
            )
        }),
        ('Promedios y Calificaciones', {
            'fields': (
                'prom_primer_parcial',
                'prom_segundo_parcial',
                'prom_tercer_parcial',
                'examen_final',
                'prom_final_calculado'
            ),
            'description': 'Los promedios se calculan automáticamente al guardar'
        }),
        ('Estado', {
            'fields': ('activo',)
        })
    )
    
    # Campos de solo lectura
    readonly_fields = [
        'prom_final_calculado',
        'fecha_registro',
        'nombre_completo'
    ]
    
    # Orden por defecto
    ordering = ['matricula']
    
    # Acciones personalizadas
    actions = ['activar_alumnos', 'desactivar_alumnos', 'recalcular_promedios']
    
    def save_model(self, request, obj, form, change):
        # Recalcular promedio final antes de guardar
        if (obj.prom_primer_parcial is not None and 
            obj.prom_segundo_parcial is not None and 
            obj.prom_tercer_parcial is not None and 
            obj.examen_final is not None):
            
            prom_parciales = (float(obj.prom_primer_parcial) + 
                             float(obj.prom_segundo_parcial) + 
                             float(obj.prom_tercer_parcial)) / 3
            obj.prom_final_calculado = round((prom_parciales + float(obj.examen_final)) / 2, 1)
        
        super().save_model(request, obj, form, change)
    
    def activar_alumnos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} alumnos activados')
    activar_alumnos.short_description = "Activar alumnos seleccionados"
    
    def desactivar_alumnos(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} alumnos desactivados')
    desactivar_alumnos.short_description = "Desactivar alumnos seleccionados"
    
    def recalcular_promedios(self, request, queryset):
        count = 0
        for alumno in queryset:
            if (alumno.prom_primer_parcial is not None and 
                alumno.prom_segundo_parcial is not None and 
                alumno.prom_tercer_parcial is not None and 
                alumno.examen_final is not None):
                
                prom_parciales = (float(alumno.prom_primer_parcial) + 
                                 float(alumno.prom_segundo_parcial) + 
                                 float(alumno.prom_tercer_parcial)) / 3
                alumno.prom_final_calculado = round((prom_parciales + float(alumno.examen_final)) / 2, 1)
                alumno.save()
                count += 1
        
        self.message_user(request, f'Promedios recalculados para {count} alumnos')
    recalcular_promedios.short_description = "Recalcular promedios finales"

# Verifica que NO tengas otro @admin.register(Alumno) en el archivo
@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = (
        'alumno',
        'materia',
        'semestre',
        'p1',
        'p2',
        'p3',
        'promedio_semestral',
        'calificacion_final',
        'fecha_registro'
    )
    list_filter = ('semestre', 'materia', 'alumno__grupo')
    search_fields = ('alumno__matricula', 'alumno__primer_nombre', 'materia__nombre')
    autocomplete_fields = ['alumno', 'materia']

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'calificaciones_count')
    search_fields = ('codigo', 'nombre')
    
    def calificaciones_count(self, obj):
        return obj.calificacion_set.count()
    calificaciones_count.short_description = 'Número de Calificaciones'