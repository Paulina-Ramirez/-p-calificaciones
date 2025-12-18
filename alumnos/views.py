# alumnos/views.py - VERSIÓN COMPLETA Y CORREGIDA
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Alumno, Calificacion
from decimal import Decimal, ROUND_HALF_UP

def login_view(request):
    error = None
    if request.method == 'POST':
        matricula = request.POST.get('matricula', '').strip()
        if not matricula:
            error = "Por favor ingresa una matrícula"
        else:
            try:
                alumno = Alumno.objects.get(matricula__iexact=matricula)
                request.session.update({
                    'alumno_matricula': alumno.matricula,
                    'alumno_nombre': alumno.nombre_completo(),
                    'alumno_id': alumno.id
                })
                return redirect('calificaciones')
            except Alumno.DoesNotExist:
                error = f"Matrícula '{matricula}' no encontrada"
    return render(request, 'alumnos/login.html', {'error': error})

def formatear_calif(valor):
    """<6 = 5, >=6 redondea (.5 sube, .4 baja)"""
    if valor is None:
        return None
    try:
        # Convertir a Decimal para precisión
        decimal_valor = Decimal(str(valor))
        
        # Regla especial: si valor < 6, poner 5
        if decimal_valor < Decimal('6'):
            return 5
        
        # Redondear normalmente (.5 sube)
        redondeado = decimal_valor.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return int(redondeado)
        
    except Exception as e:
        print(f"Error en formatear_calif({valor}): {str(e)}")
        return None

def calificaciones_view(request):
    if not request.session.get('alumno_matricula'):
        return redirect('login')
    
    try:
        alumno = Alumno.objects.get(matricula=request.session['alumno_matricula'])
        calificaciones = Calificacion.objects.filter(alumno=alumno).select_related('materia')
        
        materias_data = []
        
        for calif in calificaciones:
            es_c1301 = calif.materia.codigo == 'C1301'
            
            # Parciales formateados
            p1 = formatear_calif(calif.p1) if calif.p1 is not None else None
            p2 = formatear_calif(calif.p2) if calif.p2 is not None else None
            p3 = formatear_calif(calif.p3) if calif.p3 is not None else None
            
            # Promedio de parciales (ya calculado automáticamente en el modelo)
            # Nota: el modelo ya aplica la regla <6=5 y redondeo .5 sube
            prom_parciales = calif.promedio_parciales
            
            # Examen Final (EF del Excel)
            examen_final = formatear_calif(calif.examen_final) if calif.examen_final is not None else None
            
            # Calificación Final (ya calculada automáticamente en el modelo)
            calif_final = calif.calificacion_final
            
            # Para C1301 sigue siendo 'A' (si existe esa materia)
            if es_c1301:
                calif_final_display = 'A'
            else:
                calif_final_display = calif_final
            
            materias_data.append({
                'nombre': calif.materia.nombre,
                'codigo': calif.materia.codigo,
                'parcial1': p1,
                'parcial2': p2,
                'parcial3': p3,
                'promedio_parciales': prom_parciales,
                'examen_final': examen_final,
                'calificacion_final': calif_final_display,
                'es_c1301': es_c1301,
                'estado': calif.estado,
            })
        
        # Obtener promedios generales del alumno (son propiedades calculadas)
        prom_1er_parcial = alumno.prom_1er_parcial_general
        prom_2do_parcial = alumno.prom_2do_parcial_general
        prom_3er_parcial = alumno.prom_3er_parcial_general
        prom_final_general = alumno.prom_final_general
        
        # Formatear promedios de parciales (con regla especial)
        prom_1er_formateado = formatear_calif(prom_1er_parcial) if prom_1er_parcial is not None else None
        prom_2do_formateado = formatear_calif(prom_2do_parcial) if prom_2do_parcial is not None else None
        prom_3er_formateado = formatear_calif(prom_3er_parcial) if prom_3er_parcial is not None else None
        
        # Promedio final - VALOR EXACTO con precisión decimal
        prom_final_exacto = None
        if prom_final_general is not None:
            # Usar Decimal para redondeo preciso a 1 decimal
            try:
                prom_final_exacto = Decimal(str(prom_final_general)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            except:
                # Fallback si hay error
                prom_final_exacto = round(prom_final_general, 1)
        
        # Depuración (opcional - remover después)
        print(f"\n=== DEPURACIÓN VISTA ===")
        print(f"Alumno: {alumno.matricula}")
        print(f"Calificaciones encontradas: {calificaciones.count()}")
        print(f"Promedio 1er parcial: {prom_1er_parcial} -> {prom_1er_formateado}")
        print(f"Promedio 2do parcial: {prom_2do_parcial} -> {prom_2do_formateado}")
        print(f"Promedio 3er parcial: {prom_3er_parcial} -> {prom_3er_formateado}")
        print(f"Promedio final general: {prom_final_general} -> {prom_final_exacto}")
        
        context = {
            'alumno': alumno,
            'materias': materias_data,
            'prom_1er_parcial': prom_1er_formateado,
            'prom_2do_parcial': prom_2do_formateado,
            'prom_3er_parcial': prom_3er_formateado,
            'promedio_final': prom_final_exacto,
        }
        
        return render(request, 'alumnos/calificaciones.html', context)
        
    except Alumno.DoesNotExist:
        messages.error(request, "Alumno no encontrado en la base de datos")
        return redirect('login')
    except Exception as e:
        print(f"Error en calificaciones_view: {str(e)}")
        import traceback
        print(traceback.format_exc())
        messages.error(request, f"Error al cargar calificaciones: {str(e)}")
        return redirect('login')

def logout_view(request):
    request.session.flush()
    return redirect('login')