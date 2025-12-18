# alumnos/management/commands/importar_quinto_semestre.py
import pandas as pd
import os
import re
from django.core.management.base import BaseCommand
from alumnos.models import Alumno, Materia, Calificacion
from django.utils import timezone
from decimal import Decimal

class Command(BaseCommand):
    help = 'Importa datos desde el archivo Excel SEGUNDA PARTE.xlsx (Quinto Semestre)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'archivo_excel',
            nargs='?',
            type=str,
            default='SEGUNDA PARTE.xlsx',
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
            '--grupo',
            type=str,
            choices=['A', 'B', 'AMBOS'],
            default='AMBOS',
            help='Especificar qué grupo importar (A o B)'
        )

    def handle(self, *args, **options):
        excel_path = options['archivo_excel']
        modo_test = options['test']
        limite = options['limit']
        grupo_a_importar = options['grupo']
        
        self.stdout.write(f"Configuración:")
        self.stdout.write(f"  Archivo: {excel_path}")
        self.stdout.write(f"  Modo test: {'SÍ' if modo_test else 'NO'}")
        self.stdout.write(f"  Límite: {limite if limite > 0 else 'Todos'}")
        self.stdout.write(f"  Grupo: {grupo_a_importar}")
        self.stdout.write(f"  Fórmula promedio: Promedio simple (50% parciales + 50% examen)")
        
        if not os.path.exists(excel_path):
            self.stdout.write(self.style.ERROR(f'Archivo no encontrado: {excel_path}'))
            return
        
        try:
            # Diccionario para almacenar DataFrames de cada grupo
            grupos_df = {}
            
            if grupo_a_importar in ['A', 'AMBOS']:
                self.stdout.write("Cargando hoja QUINTO SEMESTRE A...")
                try:
                    grupo_a_df = pd.read_excel(excel_path, sheet_name='QUINTO SEMESTRE A')
                    # Limpiar nombres de columnas
                    grupo_a_df.columns = self.limpiar_nombres_columnas(grupo_a_df.columns)
                    grupos_df['A'] = grupo_a_df
                    self.stdout.write(f"  Filas cargadas: {len(grupo_a_df)}")
                    self.stdout.write(f"  Columnas: {len(grupo_a_df.columns)}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Error al cargar grupo A: {str(e)}'))
            
            if grupo_a_importar in ['B', 'AMBOS']:
                self.stdout.write("Cargando hoja Hoja2 (Grupo B)...")
                try:
                    grupo_b_df = pd.read_excel(excel_path, sheet_name='Hoja2')
                    # Limpiar nombres de columnas
                    grupo_b_df.columns = self.limpiar_nombres_columnas(grupo_b_df.columns)
                    grupos_df['B'] = grupo_b_df
                    self.stdout.write(f"  Filas cargadas: {len(grupo_b_df)}")
                    self.stdout.write(f"  Columnas: {len(grupo_b_df.columns)}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Error al cargar grupo B: {str(e)}'))
            
            if not grupos_df:
                self.stdout.write(self.style.ERROR('No se pudieron cargar datos de ningún grupo'))
                return
            
            # Procesar cada grupo
            for grupo_nombre, df in grupos_df.items():
                if modo_test:
                    self.modo_prueba(df, grupo_nombre, limite)
                else:
                    self.procesar_grupo(df, grupo_nombre, limite)
            
            if modo_test:
                self.stdout.write(self.style.SUCCESS('Modo prueba completado. No se guardó nada en la BD.'))
            else:
                self.stdout.write(self.style.SUCCESS('Importación completada exitosamente!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al importar: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def limpiar_nombres_columnas(self, columnas):
        """Limpia los nombres de columnas, manejando correctamente <br>"""
        nuevos_nombres = []
        for col in columnas:
            if isinstance(col, str):
                # Reemplazar saltos de línea y <br> por _
                col_limpia = col.replace('<br>', '_').replace('\n', '_').replace('\r', '_').strip()
                # Reemplazar múltiples espacios por uno solo
                col_limpia = re.sub(r'\s+', ' ', col_limpia)
                # Quitar espacios al final
                col_limpia = col_limpia.strip()
                nuevos_nombres.append(col_limpia)
            else:
                nuevos_nombres.append(str(col))
        return nuevos_nombres
    
    def calcular_promedio_final(self, prom_parciales, examen_final):
        """Calcula el promedio final como (prom_parciales + examen_final) / 2"""
        if prom_parciales is None or examen_final is None:
            return None
        
        try:
            promedio_final = (prom_parciales + examen_final) / 2
            return round(promedio_final, 1)
        except:
            return None
    
    def modo_prueba(self, df, grupo_nombre, limite):
        """Modo de prueba que solo analiza el archivo"""
        self.stdout.write(f"\n=== MODO PRUEBA - GRUPO {grupo_nombre} ===")
        
        # Limpiar el dataframe primero
        df_limpio = self.limpiar_dataframe(df)
        
        # Mostrar información general
        self.stdout.write(f"Total filas en DataFrame original: {len(df)}")
        self.stdout.write(f"Total filas después de limpiar: {len(df_limpio)}")
        self.stdout.write(f"Columnas: {len(df.columns)}")
        
        # Mostrar primeros registros
        self.stdout.write("\n=== PRIMEROS REGISTROS ===")
        filas_a_mostrar = min(limite if limite > 0 else 3, len(df_limpio))
        
        for i in range(filas_a_mostrar):
            row = df_limpio.iloc[i]
            matricula = self.obtener_matricula(row.get('MATRÍCULA'))
            
            if not matricula or matricula.lower() == 'nan':
                continue
            
            self.stdout.write(f"\nRegistro {i+1}:")
            self.stdout.write(f"  Matrícula: {matricula}")
            self.stdout.write(f"  Nombre: {row.get('PRIMER APELLIDO', '')} {row.get('SEGUNDO APELLIDO', '')} {row.get('NOMBRE (S)', '')}")
            self.stdout.write(f"  Grupo: {row.get('GRUPO', '')}")
            self.stdout.write(f"  Sexo: {row.get('SEXO', '')}")
            
            # Obtener valores usando búsqueda aproximada
            prom_primer_parcial = self.buscar_valor_aproximado(row, 'PROM. AL 1er PARCIAL')
            prom_segundo_parcial = self.buscar_valor_aproximado(row, 'PROM. AL 2° PARCIAL')
            prom_tercer_parcial = self.buscar_valor_aproximado(row, 'PROM. AL 3er PARCIAL')
            examen_final = self.buscar_valor_aproximado(row, 'PROM. FINAL')
            
            # Convertir a decimal
            prom_primer_parcial = self.convertir_a_decimal(prom_primer_parcial)
            prom_segundo_parcial = self.convertir_a_decimal(prom_segundo_parcial)
            prom_tercer_parcial = self.convertir_a_decimal(prom_tercer_parcial)
            examen_final = self.convertir_a_decimal(examen_final)
            
            # Calcular promedio de parciales
            prom_parciales = None
            if all(x is not None for x in [prom_primer_parcial, prom_segundo_parcial, prom_tercer_parcial]):
                prom_parciales = round((prom_primer_parcial + prom_segundo_parcial + prom_tercer_parcial) / 3, 1)
            
            # Calcular promedio final: (prom_parciales + examen_final) / 2
            prom_final_calculado = None
            if prom_parciales is not None and examen_final is not None:
                prom_final_calculado = self.calcular_promedio_final(prom_parciales, examen_final)
            
            # Mostrar todos los valores
            self.stdout.write(f"  PROM. 1er PARCIAL: {prom_primer_parcial}")
            self.stdout.write(f"  PROM. 2° PARCIAL: {prom_segundo_parcial}")
            self.stdout.write(f"  PROM. 3er PARCIAL: {prom_tercer_parcial}")
            self.stdout.write(f"  PROMEDIO PARCIALES (P1+P2+P3)/3: {prom_parciales}")
            self.stdout.write(f"  EXAMEN FINAL (PROM. FINAL): {examen_final}")
            self.stdout.write(f"  PROMEDIO FINAL (Prom.Parciales + Examen)/2: {prom_final_calculado}")
            
            # Mostrar algunas calificaciones de ejemplo
            self.stdout.write("  Calificaciones de ejemplo (por materia):")
            
            # Buscar columnas de calificación por materia
            columnas_calif = [col for col in df.columns if isinstance(col, str) and '_P1' in col]
            
            for col_calif in columnas_calif[:3]:  # Mostrar solo primeras 3
                valor = row.get(col_calif)
                if not pd.isna(valor):
                    # Extraer código de materia
                    codigo_materia = col_calif.split('_')[0]
                    self.stdout.write(f"    {codigo_materia} P1: {valor}")
    
    def buscar_valor_aproximado(self, row, nombre_buscado):
        """Busca un valor por nombre de columna aproximado"""
        for col in row.index:
            if isinstance(col, str):
                # Normalizar para comparación
                col_norm = col.replace(' ', '').replace('°', '').replace('.', '').upper()
                busc_norm = nombre_buscado.replace(' ', '').replace('°', '').replace('.', '').upper()
                
                if busc_norm in col_norm:
                    valor = row[col]
                    if not pd.isna(valor):
                        return valor
        return None
    
    def limpiar_dataframe(self, df):
        """Limpia el dataframe eliminando filas vacías"""
        df_limpio = df.copy()
        
        # Eliminar filas completamente vacías
        df_limpio = df_limpio.dropna(how='all')
        
        # Eliminar filas que no tienen matrícula (descripciones de materias)
        mask = df_limpio['MATRÍCULA'].apply(lambda x: not pd.isna(x) and str(x).strip() != '')
        df_limpio = df_limpio[mask]
        
        # Eliminar filas donde la matrícula parece ser código de materia (comienza con 'C')
        mask = df_limpio['MATRÍCULA'].apply(
            lambda x: not isinstance(x, str) or not x.strip().startswith('C')
        )
        df_limpio = df_limpio[mask]
        
        return df_limpio
    
    def procesar_grupo(self, df, grupo_nombre, limite):
        """Procesa un DataFrame de un grupo específico"""
        self.stdout.write(f'\nProcesando grupo: {grupo_nombre}')
        
        # Limpiar el dataframe primero
        df_limpio = self.limpiar_dataframe(df)
        
        if len(df_limpio) == 0:
            self.stdout.write(self.style.WARNING(f'No hay datos válidos para procesar en el grupo {grupo_nombre}'))
            return
        
        # Contadores para estadísticas
        alumnos_creados = 0
        alumnos_actualizados = 0
        materias_creadas = 0
        calificaciones_creadas = 0
        calificaciones_actualizadas = 0
        
        # Primero, crear todas las materias del grupo
        materias_dict = self.crear_materias_desde_dataframe(df, grupo_nombre)
        materias_creadas = len(materias_dict)
        
        # Determinar cuántas filas procesar
        total_filas = len(df_limpio)
        if limite > 0:
            total_filas = min(limite, total_filas)
        
        self.stdout.write(f'Procesando {total_filas} de {len(df_limpio)} filas...')
        
        # Iterar por cada fila (alumno)
        for index in range(total_filas):
            row = df_limpio.iloc[index]
            
            # Crear o actualizar alumno
            alumno, created = self.crear_o_actualizar_alumno(row, grupo_nombre)
            
            if alumno:
                if created:
                    alumnos_creados += 1
                else:
                    alumnos_actualizados += 1
                
                # Para cada materia, crear calificación
                for codigo_materia, materia_obj in materias_dict.items():
                    calificacion, calif_created = self.crear_calificacion(row, alumno, materia_obj, grupo_nombre, codigo_materia)
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
            f'\nESTADÍSTICAS - GRUPO {grupo_nombre}:'
        ))
        self.stdout.write(f'  Alumnos creados: {alumnos_creados}')
        self.stdout.write(f'  Alumnos actualizados: {alumnos_actualizados}')
        self.stdout.write(f'  Materias: {materias_creadas}')
        self.stdout.write(f'  Calificaciones creadas: {calificaciones_creadas}')
        self.stdout.write(f'  Calificaciones actualizadas: {calificaciones_actualizadas}')
    
    def crear_materias_desde_dataframe(self, df, grupo_nombre):
        """Identifica y crea las materias a partir del DataFrame"""
        materias_dict = {}
        
        # Primero identificar todos los códigos únicos
        codigos_materias = self.identificar_materias(df, grupo_nombre)
        
        self.stdout.write(f'Códigos de materia identificados en grupo {grupo_nombre}: {len(codigos_materias)}')
        self.stdout.write(f'Códigos: {sorted(list(codigos_materias))}')
        
        for codigo in codigos_materias:
            if codigo not in materias_dict:
                try:
                    nombre_materia = self.obtener_nombre_materia(df, codigo, grupo_nombre)
                    
                    materia, created = Materia.objects.get_or_create(
                        codigo=codigo,
                        defaults={'nombre': nombre_materia}
                    )
                    materias_dict[codigo] = materia
                    
                    if created:
                        self.stdout.write(f'  ✓ Materia creada: {codigo} - {nombre_materia}')
                    else:
                        self.stdout.write(f'  ↻ Materia existente: {codigo} - {materia.nombre}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ✗ Error con materia {codigo}: {str(e)}'))
        
        return materias_dict
    
    def identificar_materias(self, df, grupo_nombre):
        """Identifica correctamente los códigos de materia para el formato del archivo"""
        materias = set()
        
        for columna in df.columns:
            if isinstance(columna, str):
                # Buscar patrones como C5300_P1, C5300_P2, etc.
                patrones = [
                    r'^(C\d{4})_P[1-3]$',      # C5300_P1
                    r'^(C\d{4})_PP$',          # C5300_PP
                    r'^(C\d{4})_EF$',          # C5300_EF
                    r'^(C\d{4})_CF$',          # C5300_CF
                ]
                
                for patron in patrones:
                    match = re.match(patron, columna.strip())
                    if match:
                        codigo = match.group(1)
                        materias.add(codigo)
                        break
        
        return materias
    
    def obtener_nombre_materia(self, df, codigo, grupo_nombre):
        """Intenta obtener el nombre de la materia desde las filas inferiores del DataFrame"""
        # Buscar en las últimas filas (donde normalmente están los nombres de materias)
        for index in range(len(df)-1, max(len(df)-50, 0), -1):
            row = df.iloc[index]
            
            # Buscar filas sin matrícula (probablemente descripción de materias)
            matricula = row.get('MATRÍCULA')
            if pd.isna(matricula) or str(matricula).strip() == '':
                # Verificar si el código está en alguna columna
                for col in df.columns:
                    if col == codigo:
                        valor = row[col]
                        if not pd.isna(valor) and str(valor).strip() != '':
                            nombre = str(valor).strip()
                            if nombre and nombre.lower() != 'nan':
                                return nombre
        
        # Nombres por defecto basados en códigos comunes
        nombres_por_defecto = {
            'C5300': 'ORGANIZACIÓN PARA LA PRODUCCIÓN RURAL',
            'C5301': 'FUNDAMENTOS PARA LA ADMINISTRACIÓN RURAL',
            'C5302': 'SISTEMAS DE PRODUCCIÓN COMUNITARIA',
            'C5303': 'EDUCACIÓN AMBIENTAL',
            'C5024': 'MÉXICO EN LA HISTORIA UNIVERSAL',
            'C5125': 'DERECHO DE LOS PUEBLOS INDÍGENAS',
            'C5135': 'ECOLOGÍA',
            'C5142': 'CÁLCULO INTEGRAL',
            'C5262': 'PROYECTO I',
            'C5100': 'EXPRESIÓN ORAL Y ESCRITA EN LENGUA INDÍGENA I',
            'C5101': 'PRINCIPIOS BÁSICOS DE INTERPRETACIÓN',
            'C5102': 'EXPRESIÓN ORAL Y ESCRITA EN ESPAÑOL I',
            'C5103': 'ESPECIALIZACIÓN EN EL ÁMBITO JURÍDICO',
        }
        
        return nombres_por_defecto.get(codigo, f'Materia {codigo}')
    
    def obtener_matricula(self, valor):
        """Convierte la matrícula a string sin decimales"""
        if pd.isna(valor):
            return ''
        
        try:
            # Si es un número flotante, convertirlo a int
            if isinstance(valor, float):
                if valor.is_integer():
                    return str(int(valor))
                else:
                    return str(valor)
            
            # Si es un número entero
            if isinstance(valor, int):
                return str(valor)
            
            # Si es una cadena
            valor_str = str(valor).strip()
            
            # Remover .0 si está al final
            if valor_str.endswith('.0'):
                valor_str = valor_str[:-2]
            
            return valor_str
            
        except Exception:
            return str(valor).strip()
    
    def crear_o_actualizar_alumno(self, row, grupo_nombre):
        """Crea o actualiza un alumno a partir de una fila del DataFrame"""
        try:
            matricula_raw = row.get('MATRÍCULA')
            matricula = self.obtener_matricula(matricula_raw)
            
            if not matricula:
                self.stdout.write(self.style.WARNING(f'Matrícula vacía en fila, saltando...'))
                return None, False
            
            # Parsear nombres
            primer_apellido = str(row.get('PRIMER APELLIDO', '')).strip()
            segundo_apellido = str(row.get('SEGUNDO APELLIDO', '')).strip()
            nombres_completos = str(row.get('NOMBRE (S)', '')).strip()
            
            # Dividir nombres
            nombres = nombres_completos.split() if nombres_completos else []
            primer_nombre = nombres[0] if len(nombres) > 0 else ''
            segundo_nombre = ' '.join(nombres[1:]) if len(nombres) > 1 else ''
            
            # Grupo
            grupo = str(row.get('GRUPO', grupo_nombre)).strip()
            if not grupo:
                grupo = grupo_nombre
            
            # Sexo
            sexo_raw = row.get('SEXO', '')
            if pd.isna(sexo_raw):
                sexo = ''
            else:
                sexo = str(sexo_raw).strip().upper()
                if sexo not in ['H', 'M']:
                    sexo = 'H' if sexo == 'MASCULINO' else 'M' if sexo == 'FEMENINO' else ''
            
            # Semestre (siempre QUINTO para este archivo)
            semestre = 'QUINTO'
            
            # Obtener valores de promedios
            prom_primer_parcial = self.buscar_valor_aproximado(row, 'PROM. AL 1er PARCIAL')
            prom_segundo_parcial = self.buscar_valor_aproximado(row, 'PROM. AL 2° PARCIAL')
            prom_tercer_parcial = self.buscar_valor_aproximado(row, 'PROM. AL 3er PARCIAL')
            examen_final = self.buscar_valor_aproximado(row, 'PROM. FINAL')
            
            # Convertir a decimal
            prom_primer_parcial = self.convertir_a_decimal(prom_primer_parcial)
            prom_segundo_parcial = self.convertir_a_decimal(prom_segundo_parcial)
            prom_tercer_parcial = self.convertir_a_decimal(prom_tercer_parcial)
            examen_final = self.convertir_a_decimal(examen_final)
            
            # Calcular promedio de parciales
            prom_parciales = None
            if all(x is not None for x in [prom_primer_parcial, prom_segundo_parcial, prom_tercer_parcial]):
                prom_parciales = round((prom_primer_parcial + prom_segundo_parcial + prom_tercer_parcial) / 3, 1)
            
            # Calcular promedio final: (prom_parciales + examen_final) / 2
            prom_final_calculado = None
            if prom_parciales is not None and examen_final is not None:
                prom_final_calculado = self.calcular_promedio_final(prom_parciales, examen_final)
            
            # Mostrar para depuración
            self.stdout.write(f"\n  Matrícula {matricula}:")
            self.stdout.write(f"    P1={prom_primer_parcial}, P2={prom_segundo_parcial}, P3={prom_tercer_parcial}")
            self.stdout.write(f"    Prom. Parciales={prom_parciales}")
            self.stdout.write(f"    Examen Final={examen_final}")
            self.stdout.write(f"    Prom. Final Calculado=(Prom.Parciales + Examen)/2={prom_final_calculado}")
            
            # Crear o actualizar alumno
            alumno, created = Alumno.objects.update_or_create(
                matricula=matricula,
                defaults={
                    'primer_apellido': primer_apellido,
                    'segundo_apellido': segundo_apellido,
                    'primer_nombre': primer_nombre,
                    'segundo_nombre': segundo_nombre,
                    'semestre': semestre,
                    'grupo': grupo,
                    'sexo': sexo,
                    'prom_primer_parcial': prom_primer_parcial,
                    'prom_segundo_parcial': prom_segundo_parcial,
                    'prom_tercer_parcial': prom_tercer_parcial,
                    'examen_final': examen_final,  # ESTE ES EL EXAMEN FINAL (PROM. FINAL del Excel)
                    'prom_final_calculado': prom_final_calculado,  # ESTE ES EL PROMEDIO FINAL CALCULADO: (Prom.Parciales + Examen)/2
                    'activo': True,
                }
            )
            
            if created:
                self.stdout.write(f'  ✓ Alumno creado: {matricula} - {primer_nombre} {primer_apellido}')
            else:
                self.stdout.write(f'  ↻ Alumno actualizado: {matricula}')

            return alumno, created
            
        except Exception as e:
            matricula_mostrar = matricula if 'matricula' in locals() else 'DESCONOCIDA'
            self.stdout.write(self.style.ERROR(f'Error al crear alumno {matricula_mostrar}: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
            return None, False
    
    def crear_calificacion(self, row, alumno, materia, grupo_nombre, codigo_materia):
        """Crea una calificación para un alumno en una materia específica"""
        try:
            # Definir las columnas que buscamos para esta materia
            tipos_evaluaciones = {
                'p1': f'{codigo_materia}_P1',
                'p2': f'{codigo_materia}_P2',
                'p3': f'{codigo_materia}_P3',
                'promedio_semestral': f'{codigo_materia}_PP',
                'calificacion_final': f'{codigo_materia}_CF',
            }
            
            valores = {}
            
            for campo_modelo, columna_buscada in tipos_evaluaciones.items():
                if columna_buscada in row:
                    valor = row[columna_buscada]
                    if campo_modelo in ['p1', 'p2', 'p3']:
                        valores[campo_modelo] = self.convertir_a_entero(valor)
                    else:
                        valores[campo_modelo] = self.convertir_a_decimal(valor)
                else:
                    valores[campo_modelo] = None
            
            # Verificar si hay algún dato
            tiene_datos = any(val is not None for val in valores.values())
            
            if tiene_datos:
                # Mostrar datos para debug
                self.stdout.write(f"    Materia {codigo_materia}: " + 
                               f"P1={valores.get('p1')}, P2={valores.get('p2')}, " +
                               f"P3={valores.get('p3')}, PP={valores.get('promedio_semestral')}, " +
                               f"CF={valores.get('calificacion_final')}")
                
                calificacion, created = Calificacion.objects.update_or_create(
                    alumno=alumno,
                    materia=materia,
                    semestre='QUINTO',
                    defaults={
                        'p1': valores.get('p1'),
                        'p2': valores.get('p2'),
                        'p3': valores.get('p3'),
                        'promedio_semestral': valores.get('promedio_semestral'),
                        'calificacion_final': valores.get('calificacion_final'),
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
        """Convierte un valor a entero"""
        if pd.isna(valor):
            return None
        
        try:
            # Si ya es entero
            if isinstance(valor, int):
                return valor
            
            # Si es flotante
            if isinstance(valor, float):
                return int(round(valor))
            
            # Si es string
            valor_str = str(valor).strip()
            if valor_str == '':
                return None
            
            # Intentar convertir a float primero, luego a int
            return int(round(float(valor_str)))
        except:
            return None
    
    def convertir_a_decimal(self, valor):
        """Convierte un valor a Decimal"""
        if pd.isna(valor):
            return None
        
        try:
            # Si ya es Decimal
            if isinstance(valor, Decimal):
                return valor
            
            # Si es numérico
            if isinstance(valor, (int, float)):
                return round(float(valor), 2)
            
            # Si es string
            valor_str = str(valor).strip()
            if valor_str == '':
                return None
            
            # Reemplazar comas por puntos
            valor_str = valor_str.replace(',', '.')
            
            # Convertir a float y redondear
            return round(float(valor_str), 2)
        except:
            return None