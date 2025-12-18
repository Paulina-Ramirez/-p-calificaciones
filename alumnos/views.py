# alumnos/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Avg, Sum, Q
from .models import Alumno, Calificacion, Materia

def login_view(request):
    """Vista para el login con matrícula"""
    error = None
    
    if request.method == 'POST':
        matricula = request.POST.get('matricula', '').strip()
        
        if not matricula:
            error = "Por favor ingresa una matrícula"
        else:
            try:
                # Buscar alumno por matrícula (case insensitive)
                alumno = Alumno.objects.get(matricula__iexact=matricula)
                
                # Guardar en sesión
                request.session['alumno_matricula'] = alumno.matricula
                request.session['alumno_nombre'] = alumno.nombre_completo()
                request.session['alumno_id'] = alumno.id
                
                # Redirigir a calificaciones
                return redirect('calificaciones')
                
            except Alumno.DoesNotExist:
                error = f"Matrícula '{matricula}' no encontrada"
    
    return render(request, 'alumnos/login.html', {'error': error})

def calificaciones_view(request):
    """Vista de calificaciones para alumno específico - Dashboard mejorado"""
    
    # Verificar si hay sesión activa
    if not request.session.get('alumno_matricula'):
        return redirect('login')
    
    try:
        # Obtener alumno actual
        alumno = Alumno.objects.get(matricula=request.session['alumno_matricula'])
        
        # Obtener TODAS las calificaciones del alumno
        calificaciones = Calificacion.objects.filter(alumno=alumno).select_related('materia')
        
        # CALCULAR PROMEDIOS DEL ALUMNO (si los campos existen en tu modelo)
        promedio_p1 = getattr(alumno, 'prom_primer_parcial', 0) or 0
        promedio_p2 = getattr(alumno, 'prom_segundo_parcial', 0) or 0
        promedio_p3 = getattr(alumno, 'prom_tercer_parcial', 0) or 0
        examen_final = getattr(alumno, 'examen_final', 0) or 0
        
        # Calcular promedio de parciales del alumno
        if promedio_p1 and promedio_p2 and promedio_p3:
            promedio_parciales_alumno = (float(promedio_p1) + float(promedio_p2) + float(promedio_p3)) / 3
        else:
            promedio_parciales_alumno = 0
        
        # Calcular promedio final (50% parciales + 50% examen)
        if promedio_parciales_alumno and examen_final:
            promedio_final_alumno = (promedio_parciales_alumno + float(examen_final)) / 2
        else:
            promedio_final_alumno = 0
        
        # PREPARAR DATOS DE MATERIAS CON CÁLCULOS DETALLADOS
        materias_con_datos = []
        
        for calif in calificaciones:
            # Calcular promedio de la materia (promedio de P1, P2, P3)
            p1 = calif.p1 or 0
            p2 = calif.p2 or 0
            p3 = calif.p3 or 0
            
            # Solo calcular si hay al menos una calificación
            if p1 > 0 or p2 > 0 or p3 > 0:
                suma = 0
                count = 0
                
                if p1 > 0:
                    suma += float(p1)
                    count += 1
                if p2 > 0:
                    suma += float(p2)
                    count += 1
                if p3 > 0:
                    suma += float(p3)
                    count += 1
                
                promedio_materia = suma / count if count > 0 else 0
                
                # Crear diccionario con todos los datos
                materia_info = {
                    'nombre': calif.materia.nombre,
                    'codigo': getattr(calif.materia, 'codigo', ''),
                    'parcial1': float(p1) if p1 else 0,
                    'parcial2': float(p2) if p2 else 0,
                    'parcial3': float(p3) if p3 else 0,
                    'promedio': promedio_materia,
                    'calificacion_final': float(calif.calificacion_final) if calif.calificacion_final else 0,
                    'promedio_semestral': float(calif.promedio_semestral) if calif.promedio_semestral else 0,
                    # Agregar campos específicos de calificación si los necesitas
                    'materia_obj': calif.materia,
                }
                materias_con_datos.append(materia_info)
        
        # CALCULAR PROMEDIOS POR PARCIAL (basado en materias con datos)
        if materias_con_datos:
            # Calcular promedios generales de las materias
            promedio_p1_materias = sum(m['parcial1'] for m in materias_con_datos if m['parcial1'] > 0)
            count_p1 = sum(1 for m in materias_con_datos if m['parcial1'] > 0)
            
            promedio_p2_materias = sum(m['parcial2'] for m in materias_con_datos if m['parcial2'] > 0)
            count_p2 = sum(1 for m in materias_con_datos if m['parcial2'] > 0)
            
            promedio_p3_materias = sum(m['parcial3'] for m in materias_con_datos if m['parcial3'] > 0)
            count_p3 = sum(1 for m in materias_con_datos if m['parcial3'] > 0)
            
            # Promedios reales por parcial (de las materias)
            promedio_real_p1 = promedio_p1_materias / count_p1 if count_p1 > 0 else 0
            promedio_real_p2 = promedio_p2_materias / count_p2 if count_p2 > 0 else 0
            promedio_real_p3 = promedio_p3_materias / count_p3 if count_p3 > 0 else 0
            
            # Promedio final (promedio de promedios de materias)
            promedios_materias = [m['promedio'] for m in materias_con_datos if m['promedio'] > 0]
            promedio_final_materias = sum(promedios_materias) / len(promedios_materias) if promedios_materias else 0
        else:
            # Valores por defecto si no hay calificaciones
            promedio_real_p1 = 0
            promedio_real_p2 = 0
            promedio_real_p3 = 0
            promedio_final_materias = 0
        
        # CONTEXT PARA EL TEMPLATE
        context = {
            'alumno': alumno,
            'materias': materias_con_datos,
            
            # Promedios calculados del dashboard original
            'promedio_parciales': round(promedio_parciales_alumno, 1),
            'promedio_final': round(promedio_final_alumno, 1),
            'promedio_profesor': examen_final,  # Examen final del Excel
            'promedio_p1': round(promedio_real_p1, 1),
            'promedio_p2': round(promedio_real_p2, 1),
            'promedio_p3': round(promedio_real_p3, 1),
            'examen_final': examen_final,
            
            # Mantener compatibilidad con tu template original
            'promedio_p1_materias': round(promedio_real_p1, 1),
            'promedio_p2_materias': round(promedio_real_p2, 1),
            'promedio_p3_materias': round(promedio_real_p3, 1),
            'promedio_final_materias': round(promedio_final_materias, 1),
            
            # Opcional: incluir ambos cálculos
            'promedio_parciales_alumno': round(promedio_parciales_alumno, 1),
            'promedio_final_materias': round(promedio_final_materias, 1),
        }
        
        return render(request, 'alumnos/calificaciones.html', context)
        
    except Alumno.DoesNotExist:
        messages.error(request, "Alumno no encontrado")
        return redirect('login')
    except Exception as e:
        messages.error(request, f"Error al cargar calificaciones: {str(e)}")
        return redirect('login')

def logout_view(request):
    """Cerrar sesión"""
    request.session.flush()
    messages.info(request, "Sesión cerrada correctamente")
    return redirect('login')