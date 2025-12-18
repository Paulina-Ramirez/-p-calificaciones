# alumnos/admin.py - VERSIÓN CORREGIDA (sin errores de formato)
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg
from .models import Alumno, Materia, Calificacion

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'nombre_completo', 'semestre', 'grupo', 'sexo', 
                   'promedio_p1', 'promedio_p2', 'promedio_p3', 'promedio_final', 
                   'activo', 'fecha_registro')
    list_filter = ('semestre', 'grupo', 'sexo', 'activo')
    search_fields = ('matricula', 'primer_nombre', 'segundo_nombre', 
                    'primer_apellido', 'segundo_apellido')
    readonly_fields = ('fecha_registro', 'promedio_final_display', 
                      'promedio_p1_display', 'promedio_p2_display', 'promedio_p3_display')
    fieldsets = (
        ('Información personal', {
            'fields': ('matricula', 'primer_apellido', 'segundo_apellido',
                      'primer_nombre', 'segundo_nombre', 'sexo')
        }),
        ('Información académica', {
            'fields': ('semestre', 'grupo', 'activo')
        }),
        ('Promedios globales por parcial', {
            'fields': ('promedio_p1_display', 'promedio_p2_display', 'promedio_p3_display',
                      'prom_primer_parcial', 'prom_segundo_parcial', 'prom_tercer_parcial')
        }),
        ('Calificaciones finales', {
            'fields': ('examen_final', 'prom_final_calculado', 'promedio_final_display')
        }),
        ('Metadata', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',)
        }),
    )
    
    def promedio_p1(self, obj):
        """Calcula el promedio de P1 del alumno en todas sus materias"""
        promedio = Calificacion.objects.filter(alumno=obj).aggregate(
            avg=Avg('p1')
        )['avg']
        if promedio:
            promedio_redondeado = round(promedio, 1)
            color = 'green' if promedio_redondeado >= 7.0 else 'orange' if promedio_redondeado >= 6.0 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, promedio_redondeado)
        return "N/A"
    promedio_p1.short_description = 'Prom. P1'
    
    def promedio_p2(self, obj):
        """Calcula el promedio de P2 del alumno en todas sus materias"""
        promedio = Calificacion.objects.filter(alumno=obj).aggregate(
            avg=Avg('p2')
        )['avg']
        if promedio:
            promedio_redondeado = round(promedio, 1)
            color = 'green' if promedio_redondeado >= 7.0 else 'orange' if promedio_redondeado >= 6.0 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, promedio_redondeado)
        return "N/A"
    promedio_p2.short_description = 'Prom. P2'
    
    def promedio_p3(self, obj):
        """Calcula el promedio de P3 del alumno en todas sus materias"""
        promedio = Calificacion.objects.filter(alumno=obj).aggregate(
            avg=Avg('p3')
        )['avg']
        if promedio:
            promedio_redondeado = round(promedio, 1)
            color = 'green' if promedio_redondeado >= 7.0 else 'orange' if promedio_redondeado >= 6.0 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, promedio_redondeado)
        return "N/A"
    promedio_p3.short_description = 'Prom. P3'
    
    def promedio_p1_display(self, obj):
        """Campo de solo lectura para mostrar en detalle"""
        return self.promedio_p1(obj)
    promedio_p1_display.short_description = 'Promedio P1'
    
    def promedio_p2_display(self, obj):
        """Campo de solo lectura para mostrar en detalle"""
        return self.promedio_p2(obj)
    promedio_p2_display.short_description = 'Promedio P2'
    
    def promedio_p3_display(self, obj):
        """Campo de solo lectura para mostrar en detalle"""
        return self.promedio_p3(obj)
    promedio_p3_display.short_description = 'Promedio P3'
    
    def promedio_final(self, obj):
        """Muestra el promedio final con color según calificación"""
        if obj.prom_final_calculado:
            color = 'green' if obj.prom_final_calculado >= 7.0 else 'orange' if obj.prom_final_calculado >= 6.0 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, obj.prom_final_calculado)
        return "N/A"
    promedio_final.short_description = 'Prom. Final'
    
    def promedio_final_display(self, obj):
        """Campo de solo lectura para mostrar en detalle"""
        return self.promedio_final(obj)
    promedio_final_display.short_description = 'Promedio Final'

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'promedio_p1', 'promedio_p2', 
                   'promedio_p3', 'promedio_final', 'calificaciones_count')
    search_fields = ('codigo', 'nombre')
    ordering = ('codigo',)
    
    def promedio_p1(self, obj):
        """Calcula el promedio de P1 para esta materia"""
        promedio = Calificacion.objects.filter(materia=obj).aggregate(
            avg=Avg('p1')
        )['avg']
        if promedio:
            promedio_redondeado = round(promedio, 1)
            color = 'green' if promedio_redondeado >= 7.0 else 'orange' if promedio_redondeado >= 6.0 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, promedio_redondeado)
        return "N/A"
    promedio_p1.short_description = 'Prom. P1'
    
    def promedio_p2(self, obj):
        """Calcula el promedio de P2 para esta materia"""
        promedio = Calificacion.objects.filter(materia=obj).aggregate(
            avg=Avg('p2')
        )['avg']
        if promedio:
            promedio_redondeado = round(promedio, 1)
            color = 'green' if promedio_redondeado >= 7.0 else 'orange' if promedio_redondeado >= 6.0 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, promedio_redondeado)
        return "N/A"
    promedio_p2.short_description = 'Prom. P2'
    
    def promedio_p3(self, obj):
        """Calcula el promedio de P3 para esta materia"""
        promedio = Calificacion.objects.filter(materia=obj).aggregate(
            avg=Avg('p3')
        )['avg']
        if promedio:
            promedio_redondeado = round(promedio, 1)
            color = 'green' if promedio_redondeado >= 7.0 else 'orange' if promedio_redondeado >= 6.0 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, promedio_redondeado)
        return "N/A"
    promedio_p3.short_description = 'Prom. P3'
    
    def promedio_final(self, obj):
        """Calcula el promedio final para esta materia"""
        promedio = Calificacion.objects.filter(materia=obj).aggregate(
            avg=Avg('calificacion_final')
        )['avg']
        if promedio:
            promedio_redondeado = round(promedio, 1)
            color = 'green' if promedio_redondeado >= 7.0 else 'orange' if promedio_redondeado >= 6.0 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, promedio_redondeado)
        return "N/A"
    promedio_final.short_description = 'Prom. Final'
    
    def calificaciones_count(self, obj):
        """Muestra cuántas calificaciones hay para esta materia"""
        count = Calificacion.objects.filter(materia=obj).count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    calificaciones_count.short_description = 'N° Calif.'

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('alumno_matricula', 'alumno_nombre', 'materia', 'semestre', 
                   'p1_colored', 'p2_colored', 'p3_colored', 'promedio_parciales', 
                   'promedio_semestral', 'calificacion_final_colored', 'estado')
    list_filter = ('semestre', 'materia', 'materia__codigo')
    search_fields = ('alumno__matricula', 'alumno__primer_nombre', 
                    'alumno__primer_apellido', 'materia__codigo', 'materia__nombre')
    readonly_fields = ('promedio_parciales_calculado', 'estado', 'fecha_registro', 
                      'fecha_actualizacion')
    fieldsets = (
        ('Información básica', {
            'fields': ('alumno', 'materia', 'semestre')
        }),
        ('Calificaciones parciales', {
            'fields': ('p1', 'p2', 'p3', 'promedio_parciales_calculado')
        }),
        ('Calificaciones finales', {
            'fields': ('promedio_semestral', 'calificacion_final', 'estado')
        }),
        ('Metadata', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def alumno_matricula(self, obj):
        return obj.alumno.matricula
    alumno_matricula.short_description = 'Matrícula'
    alumno_matricula.admin_order_field = 'alumno__matricula'
    
    def alumno_nombre(self, obj):
        return obj.alumno.nombre_completo()
    alumno_nombre.short_description = 'Alumno'
    alumno_nombre.admin_order_field = 'alumno__primer_apellido'
    
    def p1_colored(self, obj):
        """Muestra P1 con color según calificación"""
        if obj.p1 is not None:
            color = 'green' if obj.p1 >= 7 else 'orange' if obj.p1 >= 6 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, obj.p1)
        return "N/A"
    p1_colored.short_description = 'P1'
    p1_colored.admin_order_field = 'p1'
    
    def p2_colored(self, obj):
        """Muestra P2 con color según calificación"""
        if obj.p2 is not None:
            color = 'green' if obj.p2 >= 7 else 'orange' if obj.p2 >= 6 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, obj.p2)
        return "N/A"
    p2_colored.short_description = 'P2'
    p2_colored.admin_order_field = 'p2'
    
    def p3_colored(self, obj):
        """Muestra P3 con color según calificación"""
        if obj.p3 is not None:
            color = 'green' if obj.p3 >= 7 else 'orange' if obj.p3 >= 6 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, obj.p3)
        return "N/A"
    p3_colored.short_description = 'P3'
    p3_colored.admin_order_field = 'p3'
    
    def promedio_parciales(self, obj):
        """Calcula y muestra el promedio de los 3 parciales"""
        if obj.p1 is not None and obj.p2 is not None and obj.p3 is not None:
            promedio = (obj.p1 + obj.p2 + obj.p3) / 3
            promedio_redondeado = round(promedio, 1)
            color = 'green' if promedio_redondeado >= 7.0 else 'orange' if promedio_redondeado >= 6.0 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, promedio_redondeado)
        return "N/A"
    promedio_parciales.short_description = 'Prom. Parciales'
    
    def promedio_parciales_calculado(self, obj):
        """Campo de solo lectura para mostrar en detalle"""
        return self.promedio_parciales(obj)
    promedio_parciales_calculado.short_description = 'Promedio Parciales'
    
    def calificacion_final_colored(self, obj):
        """Muestra la calificación final con color"""
        if obj.calificacion_final is not None:
            color = 'green' if obj.calificacion_final >= 7.0 else 'orange' if obj.calificacion_final >= 6.0 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                             color, obj.calificacion_final)
        return "N/A"
    calificacion_final_colored.short_description = 'Calif. Final'
    calificacion_final_colored.admin_order_field = 'calificacion_final'
    
    def estado(self, obj):
        """Muestra el estado de la calificación"""
        if obj.calificacion_final is not None:
            if obj.calificacion_final >= 7.0:
                return format_html('<span style="color: green; font-weight: bold;">✓ APROBADO</span>')
            else:
                return format_html('<span style="color: red; font-weight: bold;">✗ NO APROBADO</span>')
        return format_html('<span style="color: blue;">PENDIENTE</span>')
    estado.short_description = 'Estado'