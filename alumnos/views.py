from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Alumno

def login_view(request):
    """Vista para el login con matrícula"""
    error = None
    
    if request.method == 'POST':
        matricula = request.POST.get('matricula', '').strip()
        
        if not matricula:
            error = "Por favor ingresa una matrícula"
        else:
            try:
                # Buscar alumno por matrícula
                alumno = Alumno.objects.get(matricula=matricula)
                
                # Guardar matrícula en sesión
                request.session['alumno_matricula'] = alumno.matricula
                request.session['alumno_nombre'] = alumno.nombre
                
                # Redirigir a calificaciones
                return redirect('calificaciones')
                
            except Alumno.DoesNotExist:
                error = f"Matrícula '{matricula}' no encontrada"
    
    return render(request, 'alumnos/login.html', {'error': error})

def calificaciones_view(request):
    """Vista para mostrar calificaciones (escala 1-10)"""
    # Verificar si hay sesión activa
    matricula = request.session.get('alumno_matricula')
    
    if not matricula:
        return redirect('login')
    
    try:
        # Obtener datos del alumno
        alumno = Alumno.objects.get(matricula=matricula)
        materias = alumno.calificaciones_estructuradas
        
        # Calcular promedios por parcial (escala 1-10)
        promedio_p1 = 0
        promedio_p2 = 0
        promedio_p3 = 0
        
        count_p1 = 0
        count_p2 = 0
        count_p3 = 0
        
        for materia in materias:
            if materia['parcial1'] > 0:
                promedio_p1 += materia['parcial1']
                count_p1 += 1
            if materia['parcial2'] > 0:
                promedio_p2 += materia['parcial2']
                count_p2 += 1
            if materia['parcial3'] > 0:
                promedio_p3 += materia['parcial3']
                count_p3 += 1
        
        # Calcular promedios finales
        if count_p1 > 0:
            promedio_p1 = round(promedio_p1 / count_p1, 2)
        if count_p2 > 0:
            promedio_p2 = round(promedio_p2 / count_p2, 2)
        if count_p3 > 0:
            promedio_p3 = round(promedio_p3 / count_p3, 2)
        
        # Contexto con todos los promedios (escala 1-10)
        context = {
            'alumno': alumno,
            'matricula': alumno.matricula,
            'nombre': alumno.nombre,
            
            # Promedios (escala 1-10)
            'promedio_parciales': alumno.promedio_parciales,
            'promedio_profesor': float(alumno.promedio_profesor),
            'promedio_final': alumno.promedio_final,
            
            # Datos adicionales
            'materias': materias,
            'promedio_p1': promedio_p1,
            'promedio_p2': promedio_p2,
            'promedio_p3': promedio_p3,
            
            # Cálculo de fórmula
            'formula_texto': f"({alumno.promedio_parciales} + {float(alumno.promedio_profesor):.2f}) ÷ 2 = {alumno.promedio_final}"
        }
        
        return render(request, 'alumnos/calificaciones.html', context)
        
    except Alumno.DoesNotExist:
        request.session.flush()
        return redirect('login')
    
def logout_view(request):
    """Cerrar sesión"""
    request.session.flush()
    messages.info(request, "Sesión cerrada correctamente")
    return redirect('login')