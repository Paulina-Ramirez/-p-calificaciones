# alumnos/views.py - VERSIÓN CORREGIDA
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
                    'alumno_id': alumno.id,
                    'alumno_semestre': alumno.semestre  # Guardar semestre en sesión
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

def es_tercer_semestre(semestre):
    """Determina si el semestre es tercero (compatible con texto y número)"""
    if semestre is None:
        return False
    
    # Convertir a string para comparaciones
    semestre_str = str(semestre).upper().strip()
    
    # Verificar si es tercer semestre
    return (semestre_str == '3' or 
            semestre_str == 'TERCERO' or 
            semestre_str == '3RO' or
            'TERCERO' in semestre_str)

def calificaciones_view(request):
    if not request.session.get('alumno_matricula'):
        return redirect('login')
    
    try:
        alumno = Alumno.objects.get(matricula=request.session['alumno_matricula'])
        semestre_alumno = request.session.get('alumno_semestre')
        
        # Determinar si es tercer semestre
        excluir_c3303 = es_tercer_semestre(semestre_alumno)
        
        # Obtener todas las calificaciones
        calificaciones = Calificacion.objects.filter(alumno=alumno).select_related('materia')
        
        materias_data = []
        calificaciones_para_promedio = []  # Calificaciones que SÍ cuentan para promedios
        
        for calif in calificaciones:
            es_c1301 = calif.materia.codigo == 'C1301'
            es_c3303 = calif.materia.codigo == 'C3303'
            
            # Determinar si es materia sin promedio (mostrar 'A')
            es_sin_promedio = es_c1301 or (es_c3303 and excluir_c3303)
            
            # Parciales formateados
            p1 = formatear_calif(calif.p1) if calif.p1 is not None else None
            p2 = formatear_calif(calif.p2) if calif.p2 is not None else None
            p3 = formatear_calif(calif.p3) if calif.p3 is not None else None
            
            # Promedio de parciales (ya calculado automáticamente en el modelo)
            prom_parciales = calif.promedio_parciales
            
            # Examen Final (EF del Excel)
            examen_final = formatear_calif(calif.examen_final) if calif.examen_final is not None else None
            
            # Calificación Final (ya calculada automáticamente en el modelo)
            calif_final = calif.calificacion_final
            
            # Para C1301 y C3303 (si es tercer semestre) mostrar 'A'
            if es_sin_promedio:
                calif_final_display = 'A'
            else:
                calif_final_display = calif_final
            
            materia_data = {
                'nombre': calif.materia.nombre,
                'codigo': calif.materia.codigo,
                'parcial1': p1,
                'parcial2': p2,
                'parcial3': p3,
                'promedio_parciales': prom_parciales,
                'examen_final': examen_final,
                'calificacion_final': calif_final_display,
                'es_c1301': es_c1301,
                'es_c3303': es_c3303,
                'es_sin_promedio': es_sin_promedio,  # ¡ESTO ES LO QUE FALTABA!
                'estado': calif.estado,
            }
            
            materias_data.append(materia_data)
            
            # Determinar si la materia cuenta para promedios
            # C1301 nunca cuenta para promedios
            if not es_c1301:
                # C3303 solo cuenta si NO es tercer semestre
                if es_c3303:
                    if not excluir_c3303:  # Si NO excluimos C3303, entonces sí cuenta
                        calificaciones_para_promedio.append(calif)
                else:
                    # Para todas las demás materias (que no sean C1301 ni C3303)
                    calificaciones_para_promedio.append(calif)
            else:
                # Para depuración: mostrar que C1301 no cuenta
                print(f"Materia {calif.materia.codigo} (C1301) excluida de promedios")
        
        # DEPURACIÓN: Mostrar qué materias se están considerando
        print(f"\n=== MATERIAS PARA PROMEDIOS ===")
        for calif in calificaciones_para_promedio:
            print(f"- {calif.materia.codigo}: {calif.calificacion_final}")
        
        # Calcular promedios de parciales usando solo las calificaciones que cuentan
        from django.db.models import Avg
        
        if calificaciones_para_promedio:
            # Calcular promedios de parciales
            p1_valores = [calif.p1 for calif in calificaciones_para_promedio if calif.p1 is not None]
            p2_valores = [calif.p2 for calif in calificaciones_para_promedio if calif.p2 is not None]
            p3_valores = [calif.p3 for calif in calificaciones_para_promedio if calif.p3 is not None]
            
            prom_1er_parcial = sum(p1_valores) / len(p1_valores) if p1_valores else None
            prom_2do_parcial = sum(p2_valores) / len(p2_valores) if p2_valores else None
            prom_3er_parcial = sum(p3_valores) / len(p3_valores) if p3_valores else None
        else:
            prom_1er_parcial = None
            prom_2do_parcial = None
            prom_3er_parcial = None
        
        # CALCULAR PROMEDIO FINAL CORRECTAMENTE
        prom_final_general = None
        
        if calificaciones_para_promedio:
            # Obtener solo las calificaciones finales que existen y no son nulas
            califs_finales_valores = []
            materias_incluidas = []
            for calif in calificaciones_para_promedio:
                if calif.calificacion_final is not None:
                    califs_finales_valores.append(calif.calificacion_final)
                    materias_incluidas.append(calif.materia.codigo)
            
            if califs_finales_valores:
                # Sumar todas las calificaciones finales
                suma_califs_finales = sum(califs_finales_valores)
                
                # Contar cuántas materias se están promediando
                cantidad_materias = len(califs_finales_valores)
                
                # Calcular el promedio
                prom_final_general = suma_califs_finales / cantidad_materias
                
                print(f"\n=== CÁLCULO PROMEDIO FINAL ===")
                print(f"Semestre: {semestre_alumno}")
                print(f"¿Excluir C3303? {excluir_c3303}")
                print(f"Materias para promedio: {cantidad_materias}")
                print(f"Materias específicas: {materias_incluidas}")
                print(f"Calificaciones finales: {califs_finales_valores}")
                print(f"Suma total: {suma_califs_finales}")
                print(f"Promedio calculado: {prom_final_general}")
        
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
        print(f"\n=== RESUMEN FINAL ===")
        print(f"Alumno: {alumno.matricula}")
        print(f"Semestre: {semestre_alumno}")
        print(f"¿Excluir C3303? {excluir_c3303}")
        print(f"Total materias: {calificaciones.count()}")
        print(f"Materias para promedios: {len(calificaciones_para_promedio)}")
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
            'excluir_c3303': excluir_c3303,
            'cantidad_materias_promedio': len(calificaciones_para_promedio),  # Para depuración
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