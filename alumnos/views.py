# alumnos/views.py - VERSIÓN MODIFICADA
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Avg
from decimal import Decimal, ROUND_HALF_UP
from .models import Alumno, Calificacion

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

def redondear_sin_decimal(valor):
    """Redondea calificaciones sin decimales: .5 sube, .4 baja"""
    if not valor or valor == 0:
        return 0
    
    # Convertir a Decimal para mayor precisión
    decimal_valor = Decimal(str(valor))
    
    # Aplicar redondeo: .5 sube, .4 baja sin decimales
    rounded = decimal_valor.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    
    return int(rounded)

def calificaciones_view(request):
    """Vista de calificaciones para alumno específico"""
    
    # Verificar si hay sesión activa
    if not request.session.get('alumno_matricula'):
        return redirect('login')
    
    try:
        # Obtener alumno actual
        alumno = Alumno.objects.get(matricula=request.session['alumno_matricula'])
        
        # Obtener TODAS las calificaciones del alumno, INCLUYENDO C1301
        calificaciones = Calificacion.objects.filter(alumno=alumno).select_related('materia')
        
        # CALCULAR PROMEDIOS DEL ALUMNO (para tarjetas superiores - con un decimal)
        promedio_p1 = float(alumno.prom_primer_parcial) if alumno.prom_primer_parcial else 0
        promedio_p2 = float(alumno.prom_segundo_parcial) if alumno.prom_segundo_parcial else 0
        promedio_p3 = float(alumno.prom_tercer_parcial) if alumno.prom_tercer_parcial else 0
        examen_final = float(alumno.examen_final) if alumno.examen_final else 0
        
        # Calcular promedio de parciales del alumno (con un decimal)
        if promedio_p1 and promedio_p2 and promedio_p3:
            promedio_parciales = (promedio_p1 + promedio_p2 + promedio_p3) / 3
        else:
            promedio_parciales = 0
        
        # Calcular promedio final (50% parciales + 50% examen) - con un decimal
        if promedio_parciales and examen_final:
            promedio_final = (promedio_parciales + examen_final) / 2
        else:
            promedio_final = 0
        
        # PREPARAR DATOS DE MATERIAS
        materias_data = []
        materias_para_promedio = []  # Solo para calcular promedios generales (excluyendo C1301)
        
        for calif in calificaciones:
            # Obtener calificaciones de parciales
            p1 = calif.p1 or 0
            p2 = calif.p2 or 0
            p3 = calif.p3 or 0
            
            # Redondear calificaciones individuales SIN decimales
            p1_redondeado = redondear_sin_decimal(p1)
            p2_redondeado = redondear_sin_decimal(p2)
            p3_redondeado = redondear_sin_decimal(p3)
            
            # Determinar si es C1301
            es_c1301 = calif.materia.codigo == 'C1301'
            
            # Para C1301, el promedio es 'A', para otras materias calcularlo
            if es_c1301:
                promedio_materia = 'A'
            else:
                # Calcular promedio de la materia
                calificaciones_parciales = []
                if p1_redondeado > 0: calificaciones_parciales.append(p1_redondeado)
                if p2_redondeado > 0: calificaciones_parciales.append(p2_redondeado)
                if p3_redondeado > 0: calificaciones_parciales.append(p3_redondeado)
                
                if calificaciones_parciales:
                    promedio_calculado = sum(calificaciones_parciales) / len(calificaciones_parciales)
                    # Redondear el promedio de la materia SIN decimales
                    promedio_materia = redondear_sin_decimal(promedio_calculado)
                else:
                    promedio_materia = 0
            
            # Crear diccionario con los datos
            materia_info = {
                'nombre': calif.materia.nombre,
                'codigo': calif.materia.codigo,
                'parcial1': p1_redondeado,
                'parcial2': p2_redondeado,
                'parcial3': p3_redondeado,
                'promedio': promedio_materia,
                'es_c1301': es_c1301
            }
            materias_data.append(materia_info)
            
            # Agregar a lista para promedios generales solo si NO es C1301
            if not es_c1301:
                materias_para_promedio.append(materia_info)
        
        # CALCULAR PROMEDIOS POR PARCIAL (basado en materias, excluyendo C1301)
        # Solo considerar materias con calificaciones > 0 y que no sean C1301
        if materias_para_promedio:
            # Filtrar materias con calificaciones en cada parcial
            materias_con_p1 = [m for m in materias_para_promedio if m['parcial1'] > 0]
            materias_con_p2 = [m for m in materias_para_promedio if m['parcial2'] > 0]
            materias_con_p3 = [m for m in materias_para_promedio if m['parcial3'] > 0]
            
            # Calcular promedios generales (redondeados SIN decimales)
            promedio_general_p1 = redondear_sin_decimal(
                sum(m['parcial1'] for m in materias_con_p1) / len(materias_con_p1) 
                if materias_con_p1 else 0
            )
            promedio_general_p2 = redondear_sin_decimal(
                sum(m['parcial2'] for m in materias_con_p2) / len(materias_con_p2) 
                if materias_con_p2 else 0
            )
            promedio_general_p3 = redondear_sin_decimal(
                sum(m['parcial3'] for m in materias_con_p3) / len(materias_con_p3) 
                if materias_con_p3 else 0
            )
        else:
            promedio_general_p1 = promedio_general_p2 = promedio_general_p3 = 0
        
        # CONTEXT PARA EL TEMPLATE
        context = {
            'alumno': alumno,
            'materias': materias_data,
            
            # Promedios principales (con un decimal)
            'promedio_parciales': round(promedio_parciales, 1),
            'promedio_final': round(promedio_final, 1),
            'examen_final': round(examen_final, 1),
            
            # Promedios por parcial (sin decimales)
            'promedio_p1': promedio_general_p1,
            'promedio_p2': promedio_general_p2,
            'promedio_p3': promedio_general_p3,
            
            # Para compatibilidad
            'promedio_p1_materias': promedio_general_p1,
            'promedio_p2_materias': promedio_general_p2,
            'promedio_p3_materias': promedio_general_p3,
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