from django.db import models

class Alumno(models.Model):
    # Información básica
    matricula = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="Matrícula"
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre completo"
    )
    
    # Campo para las calificaciones (AHORA EN ESCALA 1-10)
    # Formato: "Materia:P1:P2:P3, Materia:P1:P2:P3"
    # Ejemplo: "Matemáticas:8.5:9.0:8.8, Español:9.0:8.5:9.2"
    calificaciones_texto = models.TextField(
        verbose_name="Calificaciones (P1:P2:P3) - Escala 1-10",
        help_text="Formato: Materia:Parcial1:Parcial2:Parcial3, ... (Escala 1-10)",
        default="",
        blank=True
    )
    
    # Promedio que el profesor asigna (también en escala 1-10)
    promedio_profesor = models.DecimalField(
        max_digits=4,  # Cambiado de 5 a 4 (máximo 10.00)
        decimal_places=2,
        default=0.00,
        verbose_name="Promedio del profesor (1-10)",
        help_text="Promedio adicional que el profesor asigna al alumno (Escala 1-10)"
    )
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    # Método para calcular promedio de los parciales (escala 1-10)
    @property
    def promedio_parciales(self):
        materias = self.calificaciones_estructuradas
        if not materias:
            return 0.00
        
        total_promedios = 0
        materias_con_calificaciones = 0
        
        for materia in materias:
            if materia['promedio'] > 0:
                total_promedios += materia['promedio']
                materias_con_calificaciones += 1
        
        if materias_con_calificaciones > 0:
            return round(total_promedios / materias_con_calificaciones, 2)
        return 0.00
    
    # Método para calcular promedio final (escala 1-10)
    @property
    def promedio_final(self):
        promedio_parciales = self.promedio_parciales
        promedio_profesor = float(self.promedio_profesor)
        
        # Validar que estén en rango 0-10
        promedio_parciales = max(0, min(10, promedio_parciales))
        promedio_profesor = max(0, min(10, promedio_profesor))
        
        # Si no hay calificaciones de parciales, usar solo el del profesor
        if promedio_parciales == 0 and promedio_profesor > 0:
            return round(promedio_profesor, 2)
        
        # Si no hay promedio del profesor, usar solo los parciales
        if promedio_profesor == 0 and promedio_parciales > 0:
            return round(promedio_parciales, 2)
        
        # Si hay ambos, calcular promedio
        if promedio_parciales > 0 and promedio_profesor > 0:
            return round((promedio_parciales + promedio_profesor) / 2, 2)
        
        return 0.00
    
    # Método para obtener calificaciones estructuradas (escala 1-10)
    @property
    def calificaciones_estructuradas(self):
        resultado = []
        if not self.calificaciones_texto:
            return resultado
        
        try:
            materias = self.calificaciones_texto.split(',')
            
            for materia_str in materias:
                materia_str = materia_str.strip()
                if not materia_str:
                    continue
                
                partes = materia_str.split(':')
                
                if len(partes) >= 4:
                    nombre_materia = partes[0].strip()
                    
                    try:
                        # Convertir a float y validar rango 0-10
                        p1 = min(10, max(0, float(partes[1].strip()) if partes[1].strip() else 0))
                        p2 = min(10, max(0, float(partes[2].strip()) if partes[2].strip() else 0))
                        p3 = min(10, max(0, float(partes[3].strip()) if partes[3].strip() else 0))
                    except ValueError:
                        continue
                    
                    # Calcular promedio de la materia (escala 1-10)
                    parciales_validos = [p for p in [p1, p2, p3] if p > 0]
                    if parciales_validos:
                        promedio_materia = sum(parciales_validos) / len(parciales_validos)
                    else:
                        promedio_materia = 0
                    
                    # Determinar color según promedio (escala 1-10)
                    color = self._obtener_color_10(promedio_materia)
                    
                    resultado.append({
                        'nombre': nombre_materia,
                        'parcial1': p1,
                        'parcial2': p2,
                        'parcial3': p3,
                        'promedio': round(promedio_materia, 2),
                        'color': color,
                        'estado': self._obtener_estado_10(promedio_materia)
                    })
                
        except Exception as e:
            print(f"Error procesando calificaciones: {e}")
        
        return resultado
    
    # Métodos auxiliares para escala 1-10
    def _obtener_color_10(self, promedio):
        if promedio >= 9.0:
            return 'success'      # Excelente
        elif promedio >= 8.0:
            return 'primary'      # Muy bien
        elif promedio >= 7.0:
            return 'warning'      # Bien
        elif promedio >= 6.0:
            return 'info'         # Regular
        elif promedio > 0:
            return 'danger'       # Reprobado
        return 'secondary'        # Sin calificar
    
    def _obtener_estado_10(self, promedio):
        if promedio >= 9.0:
            return "Excelente"
        elif promedio >= 8.0:
            return "Muy bien"
        elif promedio >= 7.0:
            return "Bien"
        elif promedio >= 6.0:
            return "Regular"
        elif promedio > 0:
            return "Reprobado"
        return "Sin calificar"
    
    # Estado general basado en promedio final (escala 1-10)
    @property
    def estado(self):
        promedio = self.promedio_final
        return self._obtener_estado_10(promedio)
    
    # Propiedad alias para compatibilidad
    @property
    def promedio(self):
        return self.promedio_final
    
    def __str__(self):
        return f"{self.matricula} - {self.nombre}"
    
    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ['matricula']