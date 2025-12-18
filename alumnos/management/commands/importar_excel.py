# alumnos/management/commands/importar_excel.py - VERSIÓN FINAL CORREGIDA
import pandas as pd
import os
import re
from django.core.management.base import BaseCommand
from alumnos.models import Alumno, Materia, Calificacion
from decimal import Decimal, ROUND_HALF_UP

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
                # Para primer semestre, normalizar nombres: C1022P1 → C1022_P1
                primer_semestre_df.columns = self.normalizar_nombres_columnas(primer_semestre_df.columns, 'PRIMERO')
                semestres_df['PRIMERO'] = primer_semestre_df
                self.stdout.write(f"  Filas cargadas: {len(primer_semestre_df)}")
                self.stdout.write(f"  Columnas: {len(primer_semestre_df.columns)}")
            
            if semestre_a_importar in ['TERCERO', 'AMBOS']:
                self.stdout.write("Cargando hoja TERCER SEMESTRE...")
                tercer_semestre_df = pd.read_excel(excel_path, sheet_name='TERCER SEMESTRE')
                # Para tercer semestre, normalizar nombres: C3023 P1 → C3023_P1
                tercer_semestre_df.columns = self.normalizar_nombres_columnas(tercer_semestre_df.columns, 'TERCERO')
                semestres_df['TERCERO'] = tercer_semestre_df
                self.stdout.write(f"  Filas cargadas: {len(tercer_semestre_df)}")
                self.stdout.write(f"  Columnas: {len(tercer_semestre_df.columns)}")
            
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
    
    def normalizar_nombres_columnas(self, columnas, semestre_nombre):
        """Normaliza nombres de columnas: C1022P1 → C1022_P1 y C3023 P1 → C3023_P1"""
        nuevos_nombres = []
        for col in columnas:
            if isinstance(col, str):
                col_str = str(col).strip()
                
                # Para columnas de calificaciones (empiezan con C)
                if col_str.startswith('C') and len(col_str) > 5:
                    # Patrón 1: C1022P1 (sin separador)
                    patron1 = r'^(C\d{4})(P[1-3]|PP|EF|CF)$'
                    match1 = re.match(patron1, col_str)
                    
                    # Patrón 2: C3023 P1 (con espacio)
                    patron2 = r'^(C\d{4})\s+(P[1-3]|PP|EF|CF)$'
                    match2 = re.match(patron2, col_str)
                    
                    # Patrón 3: Ya está normalizado C3023_P1
                    patron3 = r'^(C\d{4})_(P[1-3]|PP|EF|CF)$'
                    match3 = re.match(patron3, col_str)
                    
                    if match1:
                        # Caso: C1022P1 → C1022_P1
                        codigo = match1.group(1)
                        tipo = match1.group(2)
                        col_normalizada = f"{codigo}_{tipo}"
                    elif match2:
                        # Caso: C3023 P1 → C3023_P1
                        codigo = match2.group(1)
                        tipo = match2.group(2)
                        col_normalizada = f"{codigo}_{tipo}"
                    elif match3:
                        # Ya está normalizado
                        col_normalizada = col_str
                    else:
                        # Otras columnas (MATRÍCULA, NOMBRE, etc.)
                        col_normalizada = col_str.replace('\n', '_').replace('\r', '_')
                        col_normalizada = re.sub(r'\s+', ' ', col_normalizada)
                else:
                    # Otras columnas
                    col_normalizada = col_str.replace('\n', '_').replace('\r', '_')
                    col_normalizada = re.sub(r'\s+', ' ', col_normalizada)
                
                nuevos_nombres.append(col_normalizada)
            else:
                nuevos_nombres.append(str(col))
        
        return nuevos_nombres
    
    def modo_prueba(self, df, semestre_nombre, limite):
        """Modo de prueba que solo analiza el archivo"""
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"MODO PRUEBA - SEMESTRE {semestre_nombre}")
        self.stdout.write(f"{'='*60}")
        
        # Mostrar columnas normalizadas
        self.stdout.write(f"\nColumnas de calificación (primeras 10):")
        columnas_calif = [col for col in df.columns if isinstance(col, str) and col.startswith('C')]
        for col in columnas_calif[:10]:
            self.stdout.write(f"  {col}")
        
        # Limpiar dataframe
        df_limpio = self.limpiar_dataframe(df)
        
        self.stdout.write(f"\nFilas totales: {len(df)}")
        self.stdout.write(f"Filas después de limpiar: {len(df_limpio)}")
        
        # Mostrar primeros registros
        filas_a_mostrar = min(limite if limite > 0 else 3, len(df_limpio))
        
        for i in range(filas_a_mostrar):
            self.mostrar_registro_prueba(df_limpio.iloc[i], semestre_nombre, i+1)
    
    def limpiar_dataframe(self, df):
        """Limpia el dataframe eliminando filas vacías"""
        df_limpio = df.copy()
        
        # Eliminar filas completamente vacías
        df_limpio = df_limpio.dropna(how='all')
        
        # Eliminar filas sin matrícula válida
        mask = df_limpio['MATRÍCULA'].apply(
            lambda x: not pd.isna(x) and str(x).strip() != '' and not str(x).strip().startswith('C')
        )
        df_limpio = df_limpio[mask]
        
        return df_limpio
    
    def mostrar_registro_prueba(self, row, semestre_nombre, num_registro):
        """Muestra un registro en modo prueba - VERSIÓN CORREGIDA"""
        matricula = self.obtener_matricula(row.get('MATRÍCULA'))
        
        if not matricula or matricula.lower() == 'nan':
            return
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"REGISTRO #{num_registro} - {matricula}")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Nombre: {row.get('PRIMER APELLIDO', '')} {row.get('SEGUNDO APELLIDO', '')} {row.get('NOMBRE (S)', '')}")
        self.stdout.write(f"Semestre: {semestre_nombre}")
        self.stdout.write(f"Grupo: {row.get('GRUPO', '')}")
        self.stdout.write(f"Sexo: {row.get('SEXO', '')}")
        
        # Diccionario para agrupar calificaciones por materia
        materias_calif = {}
        
        # Buscar todas las columnas de calificación
        for col in row.index:
            if isinstance(col, str) and col.startswith('C'):
                valor = row[col]
                if not pd.isna(valor):
                    # Intentar extraer código y tipo
                    match = re.match(r'^(C\d{4})_(P[1-3]|PP|EF|CF)$', col)
                    if match:
                        codigo = match.group(1)
                        tipo = match.group(2)
                        
                        if codigo not in materias_calif:
                            materias_calif[codigo] = {}
                        
                        materias_calif[codigo][tipo] = valor
        
        # Mostrar calificaciones agrupadas por materia
        if materias_calif:
            self.stdout.write(f"\nCALIFICACIONES POR MATERIA:")
            for codigo, califs in sorted(materias_calif.items()):
                self.stdout.write(f"\n  {codigo}:")
                tipos_desc = {'P1': '1er Parcial', 'P2': '2do Parcial', 'P3': '3er Parcial',
                             'PP': 'Prom. Parciales', 'EF': 'Examen Final', 'CF': 'Calif. Final'}
                
                for tipo in ['P1', 'P2', 'P3', 'PP', 'EF', 'CF']:
                    if tipo in califs:
                        desc = tipos_desc.get(tipo, tipo)
                        self.stdout.write(f"    {desc}: {califs[tipo]}")
        else:
            self.stdout.write(f"\n⚠ No se encontraron calificaciones para este registro")
        
        self.stdout.write(f"{'='*60}")
    
    def obtener_matricula(self, valor):
        """Convierte la matrícula a string"""
        if pd.isna(valor):
            return ''
        
        try:
            # Si es numérico
            if isinstance(valor, (int, float)):
                if isinstance(valor, float) and valor.is_integer():
                    return str(int(valor))
                return str(valor)
            
            # Si es string
            valor_str = str(valor).strip()
            
            # Remover .0 si está al final
            if valor_str.endswith('.0'):
                valor_str = valor_str[:-2]
            
            return valor_str
            
        except Exception:
            return str(valor).strip()
    
    def procesar_semestre(self, df, semestre_nombre, limite):
        """Procesa un semestre completo"""
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"PROCESANDO SEMESTRE: {semestre_nombre}")
        self.stdout.write(f"{'='*60}")
        
        # Contadores
        stats = {
            'alumnos_creados': 0,
            'alumnos_actualizados': 0,
            'materias_creadas': 0,
            'calificaciones_procesadas': 0,
            'errores': 0
        }
        
        # Diccionario de nombres de materias
        nombres_materias = self.obtener_nombres_materias(semestre_nombre)
        
        # Crear materias primero
        self.stdout.write(f"\nCreando/actualizando materias...")
        for codigo, nombre in nombres_materias.items():
            try:
                materia, created = Materia.objects.get_or_create(
                    codigo=codigo,
                    defaults={'nombre': nombre}
                )
                if created:
                    stats['materias_creadas'] += 1
                    self.stdout.write(f"  ✓ {codigo}: {nombre}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ✗ Error con {codigo}: {str(e)}"))
        
        # Limpiar dataframe
        df_limpio = self.limpiar_dataframe(df)
        
        # Determinar cuántas filas procesar
        total_filas = len(df_limpio)
        if limite > 0:
            total_filas = min(limite, total_filas)
        
        self.stdout.write(f"\nProcesando {total_filas} alumnos...")
        
        # Procesar cada alumno
        for index in range(total_filas):
            row = df_limpio.iloc[index]
            matricula = self.obtener_matricula(row.get('MATRÍCULA'))
            
            try:
                # Mostrar progreso
                if (index + 1) % 5 == 0:
                    self.stdout.write(f"  Progreso: {index + 1}/{total_filas} alumnos")
                
                # Crear o actualizar alumno
                alumno, created = self.crear_o_actualizar_alumno(row, semestre_nombre, matricula)
                
                if not alumno:
                    stats['errores'] += 1
                    continue
                
                if created:
                    stats['alumnos_creados'] += 1
                    self.stdout.write(f"\n  [+] Alumno NUEVO: {matricula}")
                else:
                    stats['alumnos_actualizados'] += 1
                    self.stdout.write(f"\n  [↻] Alumno ACTUALIZADO: {matricula}")
                
                # Procesar calificaciones para este alumno
                califs_alumno = 0
                for codigo in nombres_materias.keys():
                    try:
                        materia = Materia.objects.get(codigo=codigo)
                        calif_creada = self.crear_calificacion(row, alumno, materia, codigo)
                        if calif_creada:
                            stats['calificaciones_procesadas'] += 1
                            califs_alumno += 1
                    except Materia.DoesNotExist:
                        continue
                    except Exception as e:
                        # Error silencioso para materias sin datos
                        pass
                
                if califs_alumno > 0:
                    self.stdout.write(f"    ✓ {califs_alumno} calificaciones procesadas")
                else:
                    self.stdout.write(f"    ⚠ Sin calificaciones encontradas")
                    
            except Exception as e:
                stats['errores'] += 1
                self.stdout.write(self.style.ERROR(f"\n  [✗] Error en alumno {matricula}: {str(e)}"))
        
        # Estadísticas
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS(f"ESTADÍSTICAS - SEMESTRE {semestre_nombre}"))
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"  ✓ Alumnos creados: {stats['alumnos_creados']}")
        self.stdout.write(f"  ✓ Alumnos actualizados: {stats['alumnos_actualizados']}")
        self.stdout.write(f"  ✓ Materias: {stats['materias_creadas']}")
        self.stdout.write(f"  ✓ Calificaciones procesadas: {stats['calificaciones_procesadas']}")
        if stats['errores'] > 0:
            self.stdout.write(self.style.WARNING(f"  ⚠ Errores: {stats['errores']}"))
        self.stdout.write(f"{'='*60}")
    
    def obtener_nombres_materias(self, semestre_nombre):
        """Devuelve diccionario de códigos y nombres de materias por semestre"""
        if semestre_nombre == 'PRIMERO':
            return {
                'C1022': 'CIENCIAS NATURALES I',
                'C1081': 'CIENCIAS SOCIALES I',
                'C1041': 'CULTURA DIGITAL I',
                'C1061': 'PENSAMIENTO MATEMÁTICO I',
                'C1072': 'LENGUA Y COMUNICACIÓN I',
                'C1111': 'LENGUAS INDÍGENAS I',
                'C1071': 'INGLÉS I',
                'C1083': 'PENSAMIENTO FILOSÓFICO Y HUMANIDADES I',
                'C1181': 'LABORATORIO DE INVESTIGACIÓN',
                'C1131': 'DESARROLLO COMUNITARIO I',
                'C1301': 'FORMACIÓN SOCIOEMOCIONAL I',
            }
        elif semestre_nombre == 'TERCERO':
            return {
                'C3023': 'CIENCIAS NATURALES III',
                'C3063': 'PENSAMIENTO MATEMÁTICO III',
                'C3076': 'LENGUA Y COMUNICACIÓN III',
                'C3113': 'LENGUAS INDÍGENAS III',
                'C3075': 'INGLÉS III',
                'C3085': 'PENSAMIENTO FILOSÓFICO Y HUMANIDADES III',
                'C3122': 'DESARROLLO COMUNITARIO III',
                'C3133': 'CULTURA DIGITAL III',
                'C3231': 'CIENCIAS SOCIALES III',
                'C3232': 'PROYECTO DE INVESTIGACIÓN',
                'C3303': 'FORMACIÓN SOCIOEMOCIONAL III',
            }
        else:
            return {}
    
    def crear_o_actualizar_alumno(self, row, semestre, matricula):
        """Crea o actualiza un alumno"""
        try:
            # Parsear nombres
            primer_apellido = str(row.get('PRIMER APELLIDO', '')).strip()
            segundo_apellido = str(row.get('SEGUNDO APELLIDO', '')).strip()
            nombres_completos = str(row.get('NOMBRE (S)', '')).strip()
            
            # Dividir nombres
            nombres = nombres_completos.split() if nombres_completos else []
            primer_nombre = nombres[0] if len(nombres) > 0 else ''
            segundo_nombre = ' '.join(nombres[1:]) if len(nombres) > 1 else ''
            
            # Grupo y sexo
            grupo = str(row.get('GRUPO', '')).strip()
            sexo_raw = row.get('SEXO', '')
            sexo = str(sexo_raw).strip().upper() if not pd.isna(sexo_raw) else ''
            
            # Crear alumno
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
                    'activo': True,
                }
            )
            
            return alumno, created
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error al crear alumno {matricula}: {str(e)}'))
            return None, False
    
    def crear_calificacion(self, row, alumno, materia, codigo_materia):
        """Crea una calificación para un alumno en una materia - VERSIÓN MEJORADA"""
        try:
            # Buscar todas las columnas posibles para esta materia
            tipos = {
                'p1': f'{codigo_materia}_P1',
                'p2': f'{codigo_materia}_P2',
                'p3': f'{codigo_materia}_P3',
                'examen_final': f'{codigo_materia}_EF',
            }
            
            # Obtener valores
            valores = {}
            for campo, columna in tipos.items():
                if columna in row:
                    valores[campo] = self.convertir_a_decimal(row[columna])
                else:
                    valores[campo] = None
            
            # Verificar si hay al menos un dato
            tiene_datos = any(v is not None for v in valores.values())
            
            if not tiene_datos:
                return False
            
            # Para depuración
            # self.stdout.write(f"    {codigo_materia}: P1={valores['p1']}, P2={valores['p2']}, P3={valores['p3']}, EF={valores['examen_final']}")
            
            # Crear o actualizar calificación
            calificacion, created = Calificacion.objects.update_or_create(
                alumno=alumno,
                materia=materia,
                defaults={
                    'p1': valores['p1'],
                    'p2': valores['p2'],
                    'p3': valores['p3'],
                    'examen_final': valores['examen_final'],
                }
            )
            
            # El método save() calculará automáticamente promedio_parciales y calificacion_final
            calificacion.save()
            
            return created
        
        except Exception as e:
            # Error silencioso para materias sin datos completos
            return False
    
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
                return Decimal(str(valor)).quantize(Decimal('0.1'))
            
            # Si es string
            valor_str = str(valor).strip()
            if valor_str == '':
                return None
            
            # Reemplazar comas por puntos
            valor_str = valor_str.replace(',', '.')
            
            # Convertir a Decimal con 1 decimal
            return Decimal(valor_str).quantize(Decimal('0.1'))
            
        except:
            return None