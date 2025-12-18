from django.db import models
from decimal import Decimal, ROUND_HALF_UP

class Materia(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    
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
    carrera = models.CharField(max_length=100, blank=True, null=True)  # DC o ILI
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

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
    
    @property
    def prom_1er_parcial_general(self):
        """Promedio general del 1er parcial de todas sus materias"""
        califs = self.calificaciones.all()
        if not califs:
            return None
        
        suma = 0
        count = 0
        for c in califs:
            if c.p1 is not None:
                suma += float(c.p1)
                count += 1
        
        return suma / count if count > 0 else None
    
    @property
    def prom_2do_parcial_general(self):
        """Promedio general del 1er y 2do parcial"""
        califs = self.calificaciones.all()
        if not califs:
            return None
        
        suma = 0
        count = 0
        for c in califs:
            if c.p1 is not None:
                suma += float(c.p1)
                count += 1
            if c.p2 is not None:
                suma += float(c.p2)
                count += 1
        
        return suma / count if count > 0 else None
    
    @property
    def prom_3er_parcial_general(self):
        """Promedio general de los 3 parciales"""
        califs = self.calificaciones.all()
        if not califs:
            return None
        
        suma = 0
        count = 0
        for c in califs:
            for nota in [c.p1, c.p2, c.p3]:
                if nota is not None:
                    suma += float(nota)
                    count += 1
        
        return suma / count if count > 0 else None
    
    @property
    def prom_final_general(self):
        """Promedio general de calificaciones finales (con precisión decimal)"""
        califs = self.calificaciones.all()
        if not califs:
            return None
        
        suma = Decimal('0.0')
        count = 0
        
        for c in califs:
            if c.calificacion_final is not None and c.materia.codigo != 'C1301':
                # Convertir a Decimal para precisión
                suma += Decimal(str(c.calificacion_final))
                count += 1
        
        if count == 0:
            return None
        
        # Calcular promedio con Decimal
        promedio = suma / Decimal(str(count))
        
        # Redondear a 2 decimales internamente
        return promedio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class Calificacion(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='calificaciones')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    
    # Parciales
    p1 = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    p2 = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    p3 = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    # Promedio de parciales (PP en Excel) - calculado automáticamente
    promedio_parciales = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, editable=False)
    
    # Examen final (EF en Excel)
    examen_final = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    # Calificación final (CF en Excel) - calculado automáticamente
    calificacion_final = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, editable=False)
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['alumno', 'materia']
        verbose_name_plural = "Calificaciones"
    
    def __str__(self):
        return f"{self.alumno.matricula} - {self.materia.codigo}"
    
    def calcular_promedio_parciales(self):
        """Calcula promedio de parciales con la regla del Excel:
           Si promedio < 6 → 5, luego redondea .5 hacia arriba"""
        notas = [self.p1, self.p2, self.p3]
        notas_validas = [n for n in notas if n is not None]
        
        if not notas_validas:
            return None
        
        # Calcular promedio
        promedio = sum(notas_validas) / len(notas_validas)
        
        # Regla especial: si promedio < 6, poner 5
        if promedio < 6:
            return Decimal('5.0')
        
        # Redondear normalmente (.5 sube)
        return Decimal(str(promedio)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    
    def calcular_calificacion_final(self):
        """Calcula calificación final con la misma regla:
           Promedio entre promedio_parciales y examen_final"""
        if self.promedio_parciales is None or self.examen_final is None:
            return None
        
        # Promedio simple entre ambos
        promedio = (self.promedio_parciales + self.examen_final) / 2
        
        # Regla especial: si promedio < 6, poner 5
        if promedio < 6:
            return Decimal('5.0')
        
        # Redondear normalmente
        return Decimal(str(promedio)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    
    def save(self, *args, **kwargs):
        # Calcular promedio de parciales si hay al menos una nota
        if any([self.p1, self.p2, self.p3]):
            self.promedio_parciales = self.calcular_promedio_parciales()
        
        # Calcular calificación final si hay promedio parciales y examen
        if self.promedio_parciales is not None and self.examen_final is not None:
            self.calificacion_final = self.calcular_calificacion_final()
        
        super().save(*args, **kwargs)
    
    @property
    def estado(self):
        """Estado de la calificación"""
        if self.calificacion_final is not None:
            if self.calificacion_final >= 6:
                return "Aprobado"
            else:
                return "Reprobado"
        elif self.p1 is not None:
            return "En proceso"
        else:
            return "Sin calificar"