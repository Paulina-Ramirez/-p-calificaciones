# alumnos/views.py - VERSIÓN CONCISA
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Alumno, Calificacion

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
        num = float(valor)
        if num < 6:
            return 5
        entero = int(num)
        return entero + 1 if (num - entero) >= 0.5 else entero
    except:
        return valor

def calificaciones_view(request):
    if not request.session.get('alumno_matricula'):
        return redirect('login')
    
    try:
        alumno = Alumno.objects.get(matricula=request.session['alumno_matricula'])
        calificaciones = Calificacion.objects.filter(alumno=alumno).select_related('materia')
        
        materias_data = []
        suma_finales = 0
        count_materias = 0
        
        for calif in calificaciones:
            es_c1301 = calif.materia.codigo == 'C1301'
            
            # Parciales formateados
            p1 = formatear_calif(calif.p1) or 0
            p2 = formatear_calif(calif.p2) or 0
            p3 = formatear_calif(calif.p3) or 0
            
            # Promedio de parciales
            parciales = [p for p in [p1, p2, p3] if p > 0]
            prom_parciales = formatear_calif(sum(parciales)/len(parciales)) if parciales else 0
            
            # Examen Final (promedio_semestral)
            examen_final = formatear_calif(calif.promedio_semestral) or 0
            
            # Calificación Final (calificacion_final)
            if es_c1301:
                calif_final = 'A'
                calif_valor = None
            else:
                calif_valor = calif.calificacion_final
                calif_final = formatear_calif(calif_valor) if calif_valor else 0
            
            # Para promedio general
            if not es_c1301 and calif_valor is not None:
                valor = float(calif_valor)
                suma_finales += 5 if valor < 6 else valor
                count_materias += 1
            
            materias_data.append({
                'nombre': calif.materia.nombre,
                'codigo': calif.materia.codigo,
                'parcial1': p1,
                'parcial2': p2,
                'parcial3': p3,
                'promedio_parciales': prom_parciales,
                'examen_final': examen_final,
                'calificacion_final': calif_final,
                'es_c1301': es_c1301,
            })
        
        # Promedio final general
        prom_final = suma_finales / count_materias if count_materias > 0 else 0
        prom_final = int(prom_final) if prom_final.is_integer() else round(prom_final, 1)
        
        context = {
            'alumno': alumno,
            'materias': materias_data,
            'pp': formatear_calif(alumno.prom_final_calculado) or 0,
            'ef': formatear_calif(alumno.examen_final) or 0,
            'promedio_final': prom_final,
        }
        
        return render(request, 'alumnos/calificaciones.html', context)
        
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('login')

def logout_view(request):
    request.session.flush()
    return redirect('login')