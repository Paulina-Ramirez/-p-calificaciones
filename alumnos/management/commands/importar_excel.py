# alumnos/management/commands/importar_excel.py - VERSIÓN MEJORADA
import pandas as pd
import os
import re
from django.core.management.base import BaseCommand
from alumnos.models import Alumno, Materia, Calificacion
from django.utils import timezone
from decimal import Decimal

class Command(BaseCommand):
    help = 'Importa datos desde el archivo Excel PRUEBA CALIFICACIONES WEB.xlsx'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'archivo_excel',
            nargs='?',
            type=str,
            default='PRUEBA CALIFICACIONES WEB.xlsx',
            help='Ruta del archivo Excel a importar'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Modo prueba: solo analiza el archivo sin guardar en la BD'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Límite de registros a procesar (0 para todos)'
        )
        parser.add_argument(
            '--semestre',
            type=str,
            choices=['PRIMERO', 'TERCERO', 'AMBOS'],
            default='AMBOS',
            help='Especificar qué semestre importar'
        )

    def handle(self, *args, **options):
        excel_path = options['archivo_excel']
        modo_test = options['test']
        limite = options['limit']
        semestre_a_importar = options['semestre']
        
        self.stdout.write(f"Configuración:")
        self.stdout.write(f"  Archivo: {excel_path}")
        self.stdout.write(f"  Modo test: {'SÍ' if modo_test else 'NO'}")
        self.stdout.write(f"  Límite: {limite if limite > 0 else 'Todos'}")
        self.stdout.write(f"  Semestre: {semestre_a_importar}")
        
        if not os.path.exists(excel_path):
            self.stdout.write(self.style.ERROR(f'Archivo no encontrado: {excel_path}'))
            return
        
        try:
            # Diccionario para almacenar DataFrames de cada semestre
            semestres_df = {}
            
            if semestre_a_importar in ['PRIMERO', 'AMBOS']:
                self.stdout.write("Cargando hoja PRIMER SEMESTRE...")
                primer_semestre_df = pd.read_excel(excel_path, sheet_name='PRIMER SEMESTRE')
                semestres_df['PRIMERO'] = primer_semestre_df
                self.stdout.write(f"  Filas cargadas: {len(primer_semestre_df)}")
            
            if semestre_a_importar in ['TERCERO', 'AMBOS']:
                self.stdout.write("Cargando hoja TERCER SEMESTRE...")
                tercer_semestre_df = pd.read_excel(excel_path, sheet_name='TERCER SEMESTRE')
                semestres_df['TERCERO'] = tercer_semestre_df
                self.stdout.write(f"  Filas cargadas: {len(tercer_semestre_df)}")
            
            # Procesar cada semestre
            for semestre_nombre, df in semestres_df.items():
                if modo_test:
                    self.modo_prueba(df, semestre_nombre, limite)
                else:
                    self.procesar_semestre(df, semestre_nombre, limite)
            
            if modo_test:
                self.stdout.write(self.style.SUCCESS('Modo prueba completado. No se guardó nada en la BD.'))
            else:
                self.stdout.write(self.style.SUCCESS('Importación completada exitosamente!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al importar: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def modo_prueba(self, df, semestre_nombre, limite):
        """Modo de prueba que solo analiza el archivo"""
        self.stdout.write(f"\n=== MODO PRUEBA - SEMESTRE {semestre_nombre} ===")
        
        # Mostrar información general
        self.stdout.write(f"Total filas en DataFrame: {len(df)}")
        self.stdout.write(f"Columnas: {len(df.columns)}")
        
        # Buscar columnas específicas
        columnas_buscadas = [
            'MATRÍCULA', 'NOMBRE (S)', 'GRUPO', 'SEXO',
            'PROM. AL 1er PARCIAL', 'PROM. AL 2° PARCIAL',
            'PROM. AL 3er PARCIAL', 'PROM. FINAL'
        ]
        
        self.stdout.write("\n=== VERIFICACIÓN DE COLUMNAS CLAVE ===")
        for col_buscada in columnas_buscadas:
            encontrada = False
            for col_real in df.columns:
                if isinstance(col_real, str):
                    # Buscar coincidencias aproximadas
                    if col_buscada.replace(' ', '').upper() in col_real.replace(' ', '').upper():
                        encontrada = True
                        self.stdout.write(f"  ✓ {col_buscada}: ENCONTRADA como '{col_real}'")
                        # Mostrar algunos valores de ejemplo
                        valores = []
                        for i in range(min(3, len(df))):
                            val = df.iloc[i][col_real]
                            if not pd.isna(val):
                                valores.append(f"{val}")
                        if valores:
                            self.stdout.write(f"       Ejemplos: {', '.join(valores)}")
                        break
            if not encontrada:
                self.stdout.write(f"  ✗ {col_buscada}: NO ENCONTRADA")
        
        # Mostrar tipos de datos en las primeras filas
        self.stdout.write("\n=== ANÁLISIS DE TIPOS DE DATOS ===")
        filas_a_mostrar = min(limite if limite > 0 else 3, len(df))
        
        for i in range(filas_a_mostrar):
            row = df.iloc[i]
            matricula = self.obtener_matricula(row.get('MATRÍCULA'))
            
            if not matricula or matricula.lower() == 'nan':
                continue
            
            self.stdout.write(f"\nRegistro {i+1}: {matricula}")
            
            # Mostrar algunos datos clave con sus tipos
            datos_clave = [
                ('MATRÍCULA', 'MATRÍCULA'),
                ('NOMBRE', 'NOMBRE (S)'),
                ('GRUPO', 'GRUPO'),
                ('SEXO', 'SEXO')
            ]
            
            for nombre, col in datos_clave:
                if col in row:
                    valor = row[col]
                    tipo = type(valor).__name__
                    self.stdout.write(f"  {nombre}: {valor} (tipo: {tipo})")
            
            # Mostrar algunas calificaciones de ejemplo
            self.stdout.write("  CALIFICACIONES DE EJEMPLO:")
            
            # Buscar algunas columnas de calificación
            columnas_calif_encontradas = 0
            for col in df.columns:
                if isinstance(col, str) and col.startswith('C') and 'P1' in col:
                    valor = row[col]
                    if not pd.isna(valor):
                        tipo = type(valor).__name__
                        self.stdout.write(f"    {col}: {valor} (tipo: {tipo})")
                        columnas_calif_encontradas += 1
                        if columnas_calif_encontradas >= 3:
                            break
    
    def identificar_materias(self, df):
        """Identifica correctamente los códigos de materia para ambos formatos"""
        materias = set()
        
        for columna in df.columns:
            if isinstance(columna, str) and columna.startswith('C'):
                # Para primer semestre: C1022P1, C1022P2, etc.
                # Para tercer semestre: C3023 P1, C3023 P2, etc.
                
                # Patrones para extraer el código de materia
                patrones = [
                    r'^(C\d{4})P[1-3]$',     # C1022P1
                    r'^(C\d{4}) P[1-3]$',    # C3023 P1
                    r'^(C\d{4})PP$',         # C1022PP
                    r'^(C\d{4}) PP$',        # C3023 PP
                    r'^(C\d{4})EF$',         # C1022EF
                    r'^(C\d{4}) EF$',        # C3023 EF
                    r'^(C\d{4})CF$',         # C1022CF
                    r'^(C\d{4}) CF$',        # C3023 CF
                ]
                
                for patron in patrones:
                    match = re.match(patron, columna)
                    if match:
                        codigo = match.group(1)
                        materias.add(codigo)
                        break
        
        return materias
    
    def procesar_semestre(self, df, semestre_nombre, limite):
        """Procesa un DataFrame de un semestre específico"""
        self.stdout.write(f'\nProcesando semestre: {semestre_nombre}')
        
        # Contadores para estadísticas
        alumnos_creados = 0
        alumnos_actualizados = 0
        materias_creadas = 0
        calificaciones_creadas = 0
        calificaciones_actualizadas = 0
        
        # Primero, crear todas las materias del semestre
        materias_dict = self.crear_materias_desde_dataframe(df)
        materias_creadas = len(materias_dict)
        
        # Determinar cuántas filas procesar
        total_filas = len(df)
        if limite > 0:
            total_filas = min(limite, total_filas)
        
        self.stdout.write(f'Procesando {total_filas} de {len(df)} filas...')
        
        # Iterar por cada fila (alumno)
        for index in range(total_filas):
            row = df.iloc[index]
            
            # Saltar filas vacías o sin matrícula
            matricula_raw = row.get('MATRÍCULA')
            if pd.isna(matricula_raw) or str(matricula_raw).strip() == '':
                continue
            
            # Crear o actualizar alumno (INCLUYENDO PROMEDIOS)
            alumno, created = self.crear_o_actualizar_alumno(row, semestre_nombre)
            
            if alumno:
                if created:
                    alumnos_creados += 1
                else:
                    alumnos_actualizados += 1
                
                # Para cada materia, crear calificación
                for codigo_materia, materia_obj in materias_dict.items():
                    calificacion, calif_created = self.crear_calificacion(row, alumno, materia_obj, semestre_nombre, codigo_materia)
                    if calificacion:
                        if calif_created:
                            calificaciones_creadas += 1
                        else:
                            calificaciones_actualizadas += 1
            
            # Mostrar progreso
            if (index + 1) % 10 == 0:
                self.stdout.write(f'  Procesados {index + 1} alumnos...')
        
        # Mostrar estadísticas finales
        self.stdout.write(self.style.SUCCESS(
            f'\nESTADÍSTICAS - SEMESTRE {semestre_nombre}:'
        ))
        self.stdout.write(f'  Alumnos creados: {alumnos_creados}')
        self.stdout.write(f'  Alumnos actualizados: {alumnos_actualizados}')
        self.stdout.write(f'  Materias: {materias_creadas}')
        self.stdout.write(f'  Calificaciones creadas: {calificaciones_creadas}')
        self.stdout.write(f'  Calificaciones actualizadas: {calificaciones_actualizadas}')
    
    def crear_materias_desde_dataframe(self, df):
        """Identifica y crea las materias a partir del DataFrame"""
        materias_dict = {}
        
        # Primero identificar todos los códigos únicos
        codigos_materias = self.identificar_materias(df)
        
        self.stdout.write(f'Códigos de materia identificados: {len(codigos_materias)}')
        
        for codigo in codigos_materias:
            if codigo not in materias_dict:
                try:
                    nombre_materia = self.obtener_nombre_materia(df, codigo)
                    
                    materia, created = Materia.objects.get_or_create(
                        codigo=codigo,
                        defaults={'nombre': nombre_materia}
                    )
                    materias_dict[codigo] = materia
                    
                    if created:
                        self.stdout.write(f'  Materia creada: {codigo} - {nombre_materia}')
                    else:
                        self.stdout.write(f'  Materia existente: {codigo}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Error con materia {codigo}: {str(e)}'))
        
        return materias_dict
    
    def obtener_nombre_materia(self, df, codigo):
        """Intenta obtener el nombre de la materia desde las filas inferiores del DataFrame"""
        # Buscar en las últimas filas (donde normalmente están los nombres)
        for index in range(len(df)-1, max(len(df)-30, 0), -1):
            row = df.iloc[index]
            # Buscar filas sin matrícula (probablemente descripción de materias)
            if pd.isna(row.get('MATRÍCULA')):
                # Intentar diferentes formatos de columna
                posibles_columnas = [codigo, f'{codigo} ', f'{codigo}  ']
                for col in posibles_columnas:
                    if col in df.columns:
                        valor = row.get(col)
                        if not pd.isna(valor) and str(valor).strip() != '':
                            nombre = str(valor).strip()
                            if nombre and nombre.lower() != 'nan':
                                return nombre
        
        return f'Materia {codigo}'
    
    def obtener_matricula(self, valor):
        """Convierte la matrícula a string sin decimales"""
        if pd.isna(valor):
            return ''
        
        # Si es un número, convertirlo a int primero
        try:
            if isinstance(valor, (int, float)):
                # Remover el .0 si es decimal
                if float(valor).is_integer():
                    return str(int(valor))
                return str(valor)
        except:
            pass
        
        return str(valor).strip()
    
    def buscar_columna_aproximada(self, row, posibles_nombres):
        """Busca una columna por nombre aproximado"""
        for col in row.index:
            if isinstance(col, str):
                for nombre_buscado in posibles_nombres:
                    # Buscar coincidencia aproximada
                    if nombre_buscado.replace(' ', '').upper() in col.replace(' ', '').upper():
                        return col, row[col]
        return None, None
    
    def crear_o_actualizar_alumno(self, row, semestre):
        """Crea o actualiza un alumno a partir de una fila del DataFrame - CORREGIDO"""
        try:
            matricula_raw = row.get('MATRÍCULA')
            matricula = self.obtener_matricula(matricula_raw)
            
            if not matricula:
                return None, False
            
            # Parsear nombres
            nombres_completos = str(row.get('NOMBRE (S)', '')).strip()
            nombres = nombres_completos.split() if nombres_completos else []
            
            primer_nombre = nombres[0] if len(nombres) > 0 else ''
            segundo_nombre = ' '.join(nombres[1:]) if len(nombres) > 1 else ''
            
            # Determinar el semestre
            semestre_alumno = str(row.get('SEMESTRE', semestre)).strip()
            if not semestre_alumno or semestre_alumno.lower() == 'nan':
                semestre_alumno = semestre
            
            # Grupo (convertir a string)
            grupo_raw = row.get('GRUPO', '')
            if pd.isna(grupo_raw):
                grupo = ''
            else:
                grupo = str(grupo_raw).strip()
            
            # Sexo
            sexo_raw = row.get('SEXO', '')
            if pd.isna(sexo_raw):
                sexo = ''
            else:
                sexo = str(sexo_raw).strip().upper()
                if sexo not in ['H', 'M']:
                    sexo = ''
            
            # ======================= CORREGIDO: OBTENER PROMEDIOS =======================
            
            # Leer los promedios de parciales del Excel
            prom_primer_parcial = self.obtener_promedio(row, 'PROM. AL 1ER PARCIAL')
            prom_segundo_parcial = self.obtener_promedio(row, 'PROM. AL 2° PARCIAL')
            prom_tercer_parcial = self.obtener_promedio(row, 'PROM. AL 3ER PARCIAL')
            
            # Leer examen final (PROM. FINAL en el Excel)
            examen_final = self.obtener_promedio(row, 'PROM. FINAL')
            
            # Calcular promedio final (si tenemos todos los datos)
            prom_final_calculado = None
            if (prom_primer_parcial is not None and 
                prom_segundo_parcial is not None and 
                prom_tercer_parcial is not None and 
                examen_final is not None):
                
                # CALCULAR PROMEDIO FINAL SEGÚN TU FÓRMULA
                # Aquí puedes ajustar la fórmula según tu sistema
                
                # Opción 1: Promedio simple de los tres parciales + examen
                prom_parciales = (float(prom_primer_parcial) + 
                                 float(prom_segundo_parcial) + 
                                 float(prom_tercer_parcial)) / 3
                
                # Opción 2: 70% parciales + 30% examen (ajusta los porcentajes)
                # prom_final_calculado = (prom_parciales * 0.7) + (float(examen_final) * 0.3)
                
                # Opción 3: 60% parciales + 40% examen
                # prom_final_calculado = (prom_parciales * 0.6) + (float(examen_final) * 0.4)
                
                # Opción 4: Promedio directo (50% parciales + 50% examen)
                prom_final_calculado = (prom_parciales + float(examen_final)) / 2
                
                # Redondear a 1 decimal
                prom_final_calculado = round(prom_final_calculado, 1)
            
            # Mostrar para debug
            self.stdout.write(f"  Matrícula {matricula}:")
            self.stdout.write(f"    P1={prom_primer_parcial}, P2={prom_segundo_parcial}, P3={prom_tercer_parcial}")
            self.stdout.write(f"    Examen Final={examen_final}, Prom. Calculado={prom_final_calculado}")
            
            # Crear o actualizar alumno
            alumno, created = Alumno.objects.update_or_create(
                matricula=matricula,
                defaults={
                    'primer_apellido': str(row.get('PRIMER APELLIDO', '')).strip(),
                    'segundo_apellido': str(row.get('SEGUNDO APELLIDO', '')).strip(),
                    'primer_nombre': primer_nombre,
                    'segundo_nombre': segundo_nombre,
                    'semestre': semestre_alumno,
                    'grupo': grupo,
                    'sexo': sexo,
                    'prom_primer_parcial': prom_primer_parcial,
                    'prom_segundo_parcial': prom_segundo_parcial,
                    'prom_tercer_parcial': prom_tercer_parcial,
                    'examen_final': examen_final,
                    'prom_final_calculado': prom_final_calculado,
                    'activo': True,
                }
            )

            return alumno, created
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al crear alumno {matricula}: {str(e)}'))
            import traceback
            traceback.print_exc()
            return None, False
        
    def obtener_promedio(self, row, nombre_columna):
        """Busca y convierte un promedio específico"""
        for col in row.index:
            if isinstance(col, str):
                # Buscar coincidencia aproximada
                if nombre_columna.replace(' ', '').upper() in col.replace(' ', '').upper():
                    valor = row[col]
                    return self.convertir_a_decimal(valor)
        return None
    
    def crear_calificacion(self, row, alumno, materia, semestre, codigo_materia):
        """Crea una calificación para un alumno en una materia específica - MEJORADO"""
        try:
            # Intentar diferentes formatos de nombres de columna
            # Para primer semestre: C1022P1, C1022P2, C1022P3, C1022PP, C1022EF, C1022CF
            # Para tercer semestre: C3023 P1, C3023 P2, C3023 P3, C3023 PP, C3023 EF, C3023 CF
            
            posibles_formatos = [
                # Sin espacio (primer semestre)
                (f'{codigo_materia}P1', 'p1'),
                (f'{codigo_materia}P2', 'p2'),
                (f'{codigo_materia}P3', 'p3'),
                (f'{codigo_materia}PP', 'pp'),  # Promedio parcial
                (f'{codigo_materia}EF', 'ef'),  # Examen final
                (f'{codigo_materia}CF', 'cf'),  # Calificación final
                # Con espacio (tercer semestre)
                (f'{codigo_materia} P1', 'p1'),
                (f'{codigo_materia} P2', 'p2'),
                (f'{codigo_materia} P3', 'p3'),
                (f'{codigo_materia} PP', 'pp'),
                (f'{codigo_materia} EF', 'ef'),
                (f'{codigo_materia} CF', 'cf'),
            ]
            
            valores = {}
            
            for columna, tipo in posibles_formatos:
                if columna in row.index:
                    if tipo in ['p1', 'p2', 'p3']:
                        # Para parciales: convertir a entero
                        valores[tipo] = self.convertir_a_entero(row[columna])
                    else:
                        # Para promedios y calificaciones finales: convertir a decimal
                        valores[tipo] = self.convertir_a_decimal(row[columna], es_promedio=(tipo in ['pp', 'cf']))
            
            # Verificar si hay algún dato
            tiene_datos = any(val is not None for val in valores.values())
            
            if tiene_datos:
                # Mostrar datos para debug
                self.stdout.write(f"    Materia {codigo_materia}: P1={valores.get('p1')}, P2={valores.get('p2')}, P3={valores.get('p3')}, PP={valores.get('pp')}, CF={valores.get('cf')}")
                
                calificacion, created = Calificacion.objects.update_or_create(
                    alumno=alumno,
                    materia=materia,
                    semestre=semestre,
                    defaults={
                        'p1': valores.get('p1'),
                        'p2': valores.get('p2'),
                        'p3': valores.get('p3'),
                        'promedio_semestral': valores.get('pp'),
                        'calificacion_final': valores.get('cf'),
                    }
                )
                
                return calificacion, created
            else:
                # No hay datos para esta materia
                return None, False
        
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error calificación {codigo_materia} para {alumno.matricula}: {str(e)}'))
            return None, False
    
    def convertir_a_entero(self, valor):
        """Convierte un valor a entero, manejando casos especiales"""
        if pd.isna(valor):
            return None
        
        valor_str = str(valor).strip()
        
        if valor_str in ['', '/', 'NA', 'N/A', 'nan', 'NaN', '-']:
            return None
        
        try:
            # Reemplazar comas por puntos si es necesario
            valor_str = valor_str.replace(',', '.')
            
            # Si parece ser una fórmula de Excel, intentar extraer el valor
            if valor_str.startswith('='):
                import re
                # Buscar números en la fórmula
                numeros = re.findall(r'\b\d+\b', valor_str)
                if numeros:
                    return int(float(numeros[-1]))
            
            # Intentar convertir a float primero y luego a int
            valor_float = float(valor_str)
            
            # Redondear al entero más cercano
            return int(round(valor_float))
            
        except (ValueError, TypeError):
            try:
                # Intentar extraer solo dígitos
                import re
                numeros = re.findall(r'\d+', valor_str)
                if numeros:
                    return int(numeros[0])
                return None
            except:
                return None
    
    def convertir_a_decimal(self, valor, es_promedio=False):
        """Convierte un valor a Decimal, manejando casos especiales"""
        if pd.isna(valor):
            return None
        
        valor_str = str(valor).strip()
        
        if valor_str in ['', '/', 'NA', 'N/A', 'nan', 'NaN', '-']:
            return None
        
        try:
            # Reemplazar comas por puntos si es necesario
            valor_str = valor_str.replace(',', '.')
            
            # Si parece ser una fórmula de Excel, intentar extraer el valor
            if valor_str.startswith('='):
                import re
                # Buscar números decimales en la fórmula
                numeros = re.findall(r'\d+\.?\d*', valor_str)
                if numeros:
                    # Para promedios, mantener un decimal; para otros, redondear a 1 decimal
                    valor_float = float(numeros[-1])
                    if es_promedio:
                        # Para promedios, mantener precisión
                        return round(valor_float, 2)
                    else:
                        return round(valor_float, 1)
            
            # Intentar convertir a float
            valor_float = float(valor_str)
            
            # Redondear según el tipo
            if es_promedio:
                # Para promedios, mantener un decimal
                return round(valor_float, 2)
            else:
                # Para calificaciones, redondear a 1 decimal
                return round(valor_float, 1)
                
        except (ValueError, TypeError):
            try:
                # Intentar extraer números decimales
                import re
                numeros = re.findall(r'\d+\.?\d*', valor_str)
                if numeros:
                    valor_float = float(numeros[0])
                    if es_promedio:
                        return round(valor_float, 2)
                    else:
                        return round(valor_float, 1)
                return None
            except:
                return None