# alumnos/admin.py - VERSIÓN CORREGIDA FINAL
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg
from .models import Alumno, Materia, Calificacion
from django import forms

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = '__all__'
    
    def clean_prom_primer_parcial(self):
        data = self.cleaned_data.get('prom_primer_parcial')
        if data is not None and (data < 0 or data > 10):
            raise forms.ValidationError("El promedio debe estar entre 0 y 10")
        return data
    
    def clean_prom_segundo_parcial(self):
        data = self.cleaned_data.get('prom_segundo_parcial')
        if data is not None and (data < 0 or data > 10):
            raise forms.ValidationError("El promedio debe estar entre 0 y 10")
        return data
    
    def clean_prom_tercer_parcial(self):
        data = self.cleaned_data.get('prom_tercer_parcial')
        if data is not None and (data < 0 or data > 10):
            raise forms.ValidationError("El promedio debe estar entre 0 y 10")
        return data
    
    def clean_examen_final(self):
        data = self.cleaned_data.get('examen_final')
        if data is not None and (data < 0 or data > 10):
            raise forms.ValidationError("El examen final debe estar entre 0 y 10")
        return data

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    form = AlumnoForm
    
    # Campos editables
    list_editable = [
        'semestre', 
        'grupo', 
        'sexo',
        'prom_primer_parcial', 
        'prom_segundo_parcial', 
        'prom_tercer_parcial', 
        'examen_final',
        'activo'
    ]
    
    # Campos a mostrar en la lista
    list_display = (
        'matricula', 
        'nombre_completo_admin',
        'semestre', 
        'grupo', 
        'sexo',
        'prom_primer_parcial',
        'prom_segundo_parcial',
        'prom_tercer_parcial',
        'examen_final',
        'prom_final_calculado',
        'calificaciones_count',
        'estado_color',
        'fecha_registro',
        'activo'
    )
    
    # Campos de búsqueda
    search_fields = [
        'matricula', 
        'primer_nombre', 
        'segundo_nombre',
        'primer_apellido',
        'segundo_apellido',
        'semestre', 
        'grupo'
    ]
    
    # Filtros
    list_filter = [
        'semestre',
        'grupo',
        'sexo',
        'activo',
        ('fecha_registro', admin.DateFieldListFilter),
    ]
    
    # Campos en el formulario de edición
    fieldsets = (
        ('Información Personal', {
            'fields': (
                'matricula',
                ('primer_apellido', 'segundo_apellido'),
                ('primer_nombre', 'segundo_nombre'),
                ('semestre', 'grupo', 'sexo'),
                'activo'
            )
        }),
        ('Promedios y Calificaciones', {
            'fields': (
                ('prom_primer_parcial', 'prom_segundo_parcial', 'prom_tercer_parcial'),
                ('examen_final', 'prom_final_calculado'),
            ),
            'description': 'Los promedios se calculan automáticamente al guardar'
        }),
        ('Información del Sistema', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',)
        })
    )
    
    # Campos de solo lectura
    readonly_fields = [
        'prom_final_calculado',
        'fecha_registro',
        'nombre_completo_admin'
    ]
    
    # Orden por defecto
    ordering = ['-fecha_registro', 'matricula']
    
    # Acciones personalizadas
    actions = [
        'activar_alumnos', 
        'desactivar_alumnos', 
        'recalcular_promedios',
        'exportar_a_excel'
    ]
    
    # Para mostrar muchos registros por página
    list_per_page = 50
    
    # Métodos personalizados para list_display
    def nombre_completo_admin(self, obj):
        return f"{obj.primer_apellido} {obj.primer_nombre}"
    nombre_completo_admin.short_description = 'Nombre'
    nombre_completo_admin.admin_order_field = 'primer_apellido'
    
    def calificaciones_count(self, obj):
        count = obj.calificaciones.count()
        return format_html(
            '<a href="/admin/alumnos/calificacion/?alumno__id__exact={}">{}</a>',
            obj.id,
            count
        )
    calificaciones_count.short_description = 'Calificaciones'
    
    def estado_color(self, obj):
        if obj.activo:
            return format_html(
                '<span style="color: green; font-weight: bold;">● ACTIVO</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">● INACTIVO</span>'
            )
    estado_color.short_description = 'Estado'
    
    # Sobrescribir save_model para recalcular promedio
    def save_model(self, request, obj, form, change):
        if (obj.prom_primer_parcial is not None and 
            obj.prom_segundo_parcial is not None and 
            obj.prom_tercer_parcial is not None and 
            obj.examen_final is not None):
            
            prom_parciales = (float(obj.prom_primer_parcial) + 
                             float(obj.prom_segundo_parcial) + 
                             float(obj.prom_tercer_parcial)) / 3
            obj.prom_final_calculado = round((prom_parciales + float(obj.examen_final)) / 2, 1)
        
        super().save_model(request, obj, form, change)
    
    # Acciones personalizadas
    def activar_alumnos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} alumnos activados')
    activar_alumnos.short_description = "✅ Activar alumnos seleccionados"
    
    def desactivar_alumnos(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} alumnos desactivados')
    desactivar_alumnos.short_description = "❌ Desactivar alumnos seleccionados"
    
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
        
        self.message_user(request, f'✅ Promedios recalculados para {count} alumnos')
    recalcular_promedios.short_description = "🔄 Recalcular promedios finales"
    
    def exportar_a_excel(self, request, queryset):
        self.message_user(request, f'📊 Preparando exportación de {queryset.count()} alumnos')
    exportar_a_excel.short_description = "📊 Exportar a Excel"

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'alumno_info',
        'materia_info',
        'semestre',
        'p1',
        'p2',
        'p3',
        'promedio_semestral',
        'calificacion_final',
        'fecha_registro'
    )
    
    list_editable = [
        'p1', 'p2', 'p3', 'promedio_semestral', 'calificacion_final'
    ]
    
    list_filter = (
        'semestre', 
        'materia__nombre', 
        'alumno__grupo',
        ('alumno__semestre', admin.AllValuesFieldListFilter),
    )
    
    search_fields = (
        'alumno__matricula', 
        'alumno__primer_nombre',
        'alumno__primer_apellido',
        'materia__codigo',
        'materia__nombre'
    )
    
    autocomplete_fields = ['alumno', 'materia']
    
    list_per_page = 100
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('alumno', 'materia', 'semestre')
        }),
        ('Calificaciones', {
            'fields': (
                ('p1', 'p2', 'p3'),
                ('promedio_semestral', 'calificacion_final'),
            )
        }),
    )
    
    def alumno_info(self, obj):
        return format_html(
            '<strong>{}</strong><br>{} - {}',
            obj.alumno.matricula,
            obj.alumno.nombre_completo(),
            obj.alumno.grupo
        )
    alumno_info.short_description = 'Alumno'
    alumno_info.admin_order_field = 'alumno__matricula'
    
    def materia_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.materia.codigo,
            obj.materia.nombre
        )
    materia_info.short_description = 'Materia'
    materia_info.admin_order_field = 'materia__codigo'
    
    actions = ['calcular_promedios_semestrales']
    
    def calcular_promedios_semestrales(self, request, queryset):
        count = 0
        for calificacion in queryset:
            if all(val is not None for val in [calificacion.p1, calificacion.p2, calificacion.p3]):
                promedio = (float(calificacion.p1) + float(calificacion.p2) + float(calificacion.p3)) / 3
                calificacion.promedio_semestral = round(promedio, 1)
                calificacion.save()
                count += 1
        
        self.message_user(request, f'✅ Promedios semestrales calculados para {count} calificaciones')
    calcular_promedios_semestrales.short_description = "🔄 Calcular promedios semestrales"

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 
        'nombre', 
        'calificaciones_count',
        'promedio_general',
        'alumnos_aprobados'
    )
    
    search_fields = ('codigo', 'nombre')
    ordering = ['codigo']
    
    # Campos en el formulario de edición (SIN los campos que causaban error)
    fieldsets = (
        ('Información de la Materia', {
            'fields': ('codigo', 'nombre')
        }),
    )
    
    # NO incluir métodos personalizados en readonly_fields si no son atributos del modelo
    readonly_fields = []
    
    def calificaciones_count(self, obj):
        count = obj.calificacion_set.count()
        return format_html(
            '<a href="/admin/alumnos/calificacion/?materia__id__exact={}">{}</a>',
            obj.id,
            count
        )
    calificaciones_count.short_description = 'Calificaciones'
    
    def promedio_general(self, obj):
        promedio = obj.calificacion_set.aggregate(avg=Avg('calificacion_final'))['avg']
        if promedio:
            color = "green" if promedio >= 6 else "orange" if promedio >= 5 else "red"
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
                color,
                promedio
            )
        return "-"
    promedio_general.short_description = 'Promedio General'
    
    def alumnos_aprobados(self, obj):
        aprobados = obj.calificacion_set.filter(calificacion_final__gte=6).count()
        total = obj.calificacion_set.count()
        if total > 0:
            porcentaje = (aprobados / total) * 100
            return format_html(
                '{} / {}<br><small>({:.1f}%)</small>',
                aprobados,
                total,
                porcentaje
            )
        return "-"
    alumnos_aprobados.short_description = 'Aprobados / Total'