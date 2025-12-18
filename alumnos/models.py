# alumnos/models.py - VERSIÓN SIMPLIFICADA Y FUNCIONAL
from django.db import models

class Materia(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=200)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class Alumno(models.Model):
    SEXO_CHOICES = [
        ('H', 'Hombre'),
        ('M', 'Mujer'),
    ]
    
    matricula = models.CharField(max_length=20, unique=True)
    primer_nombre = models.CharField(max_length=100, blank=True, null=True)
    segundo_nombre = models.CharField(max_length=100, blank=True, null=True)
    primer_apellido = models.CharField(max_length=100, blank=True, null=True)
    segundo_apellido = models.CharField(max_length=100, blank=True, null=True)
    semestre = models.CharField(max_length=50, blank=True, null=True)
    grupo = models.CharField(max_length=10, blank=True, null=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    prom_primer_parcial = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    prom_segundo_parcial = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    prom_tercer_parcial = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    examen_final = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    # Promedio final calculado
    prom_final_calculado = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    def __str__(self):
        return f"{self.matricula} - {self.nombre_completo()}"
    
    def nombre_completo(self):
        """Devuelve el nombre completo del alumno"""
        nombre = f"{self.primer_nombre}"
        if self.segundo_nombre:
            nombre += f" {self.segundo_nombre}"
        nombre += f" {self.primer_apellido}"
        if self.segundo_apellido:
            nombre += f" {self.segundo_apellido}"
        return nombre.strip()
    
    def calcular_promedio_final(self):
        """Calcula el promedio final basado en parciales y examen final"""
        if (self.prom_primer_parcial is not None and 
            self.prom_segundo_parcial is not None and 
            self.prom_tercer_parcial is not None and 
            self.examen_final is not None):
            
            # Promedio de los tres parciales
            prom_parciales = (float(self.prom_primer_parcial) + 
                             float(self.prom_segundo_parcial) + 
                             float(self.prom_tercer_parcial)) / 3
            
            # Calcular promedio final (70% parciales + 30% examen)
            # Ajusta esta fórmula según tus necesidades
            prom_final = (prom_parciales * 0.7) + (float(self.examen_final) * 0.3)
            
            self.prom_final_calculado = round(prom_final, 1)
            self.save()
            
            return self.prom_final_calculado
        
        return None
    
    @property
    def prom_final(self):
        """Propiedad para compatibilidad, devuelve el calculado o el examen final"""
        return self.prom_final_calculado or self.examen_final

class Calificacion(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='calificaciones')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    semestre = models.CharField(max_length=50, null=True, blank=True)  # ← MANTÉN null=True
    
    p1 = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    p2 = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    p3 = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    promedio_semestral = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    calificacion_final = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    fecha_registro = models.DateTimeField(null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['alumno', 'materia', 'semestre']
    
    def __str__(self):
        return f"{self.alumno.matricula} - {self.materia.codigo} - {self.semestre}"
    
    @property
    def promedio(self):
        notas = []
        if self.p1 is not None:
            notas.append(float(self.p1))
        if self.p2 is not None:
            notas.append(float(self.p2))
        if self.p3 is not None:
            notas.append(float(self.p3))
        
        if notas:
            return round(sum(notas) / len(notas), 1)
        return 0