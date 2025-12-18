# alumnos/management/commands/importar_quinto_semestre.py
import pandas as pd
import os
import re
from django.core.management.base import BaseCommand
from alumnos.models import Alumno, Materia, Calificacion
from django.utils import timezone
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

    def handle(self, *args, **options):
        excel_path = options['archivo_excel']
        modo_test = options['test']
        limite = options['limit']
        
        self.stdout.write(f"Configuración:")
        self.stdout.write(f"  Archivo: {excel_path}")
        self.stdout.write(f"  Modo test: {'SÍ' if modo_test else 'NO'}")
        self.stdout.write(f"  Límite: {limite if limite > 0 else 'Todos'}")
        
        if not os.path.exists(excel_path):
            self.stdout.write(self.style.ERROR(f'Archivo no encontrado: {excel_path}'))
            return
        
        try:
            # Cargar ambas hojas
            self.stdout.write("Cargando hoja QUINTO SEMESTRE DC...")
            df_dc = pd.read_excel(excel_path, sheet_name='QUINTO SEMESTRE DC')
            df_dc.columns = self.limpiar_nombres_columnas(df_dc.columns)
            
            self.stdout.write("Cargando hoja QUINTO SEMESTRE ILI...")
            df_ili = pd.read_excel(excel_path, sheet_name='QUINTO SEMESTRE ILI')
            df_ili.columns = self.limpiar_nombres_columnas(df_ili.columns)
            
            # Diccionario de nombres de materias para cada carrera
            materias_dc = {
                'C5300': 'ORGANIZACIÓN PARA LA PRODUCCIÓN RURAL',
                'C5301': 'FUNDAMENTOS PARA LA ADMINISTRACIÓN RURAL',
                'C5302': 'SISTEMAS DE PRODUCCIÓN COMUNITARIA',
                'C5303': 'EDUCACIÓN AMBIENTAL',
                'C5024': 'MÉXICO EN LA HISTORIA UNIVERSAL',
                'C5125': 'DERECHO DE LOS PUEBLOS INDÍGENAS',
                'C5135': 'ECOLOGÍA',
                'C5142': 'CÁLCULO INTEGRAL',
                'C5262': 'PROYECTO I',
            }
            
            materias_ili = {
                'C5100': 'EXPRESIÓN ORAL Y ESCRITA EN LENGUA INDÍGENA I',
                'C5101': 'PRINCIPIOS BÁSICOS DE INTERPRETACIÓN',
                'C5102': 'EXPRESIÓN ORAL Y ESCRITA EN ESPAÑOL I',
                'C5103': 'ESPECIALIZACIÓN EN EL ÁMBITO JURÍDICO',
                'C5024': 'MÉXICO EN LA HISTORIA UNIVERSAL',
                'C5125': 'DERECHOS DE LOS PUEBLOS INDÍGENAS',
                'C5135': 'ECOLOGÍA',
                'C5142': 'CÁLCULO INTEGRAL',
                'C5262': 'PROYECTO I',
            }
            
            if modo_test:
                self.modo_prueba(df_dc, df_ili, materias_dc, materias_ili, limite)
            else:
                # Importar datos de DC
                self.procesar_carrera(df_dc, 'DC', materias_dc, limite)
                # Importar datos de ILI
                self.procesar_carrera(df_ili, 'ILI', materias_ili, limite)
            
            if modo_test:
                self.stdout.write(self.style.SUCCESS('Modo prueba completado. No se guardó nada en la BD.'))
            else:
                self.stdout.write(self.style.SUCCESS('Importación completada exitosamente!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al importar: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def limpiar_nombres_columnas(self, columnas):
        """Limpia los nombres de columnas"""
        nuevos_nombres = []
        for col in columnas:
            if isinstance(col, str):
                # Reemplazar <br> y saltos de línea
                col_limpia = col.replace('<br>', '_').replace('\n', '_').replace('\r', '_').strip()
                # Remover espacios múltiples
                col_limpia = re.sub(r'\s+', ' ', col_limpia)
                nuevos_nombres.append(col_limpia)
            else:
                nuevos_nombres.append(str(col))
        return nuevos_nombres
    
    def modo_prueba(self, df_dc, df_ili, materias_dc, materias_ili, limite):
        """Modo de prueba que solo analiza el archivo"""
        self.stdout.write(f"\n=== MODO PRUEBA ===")
        
        # Procesar DC
        self.stdout.write(f"\n--- CARRERA DC ---")
        df_dc_limpio = self.limpiar_dataframe(df_dc)
        filas_a_mostrar = min(limite if limite > 0 else 2, len(df_dc_limpio))
        
        for i in range(filas_a_mostrar):
            self.mostrar_registro_prueba(df_dc_limpio.iloc[i], materias_dc, 'DC')
        
        # Procesar ILI
        self.stdout.write(f"\n--- CARRERA ILI ---")
        df_ili_limpio = self.limpiar_dataframe(df_ili)
        filas_a_mostrar = min(limite if limite > 0 else 2, len(df_ili_limpio))
        
        for i in range(filas_a_mostrar):
            self.mostrar_registro_prueba(df_ili_limpio.iloc[i], materias_ili, 'ILI')
    
    def mostrar_registro_prueba(self, row, materias_dict, carrera):
        """Muestra un registro en modo prueba"""
        matricula = self.obtener_matricula(row.get('MATRÍCULA'))
        
        if not matricula or matricula.lower() == 'nan':
            return
        
        self.stdout.write(f"\nRegistro {matricula}:")
        self.stdout.write(f"  Carrera: {carrera}")
        self.stdout.write(f"  Nombre: {row.get('PRIMER APELLIDO', '')} {row.get('SEGUNDO APELLIDO', '')} {row.get('NOMBRE (S)', '')}")
        self.stdout.write(f"  Grupo: {row.get('GRUPO', '')}")
        self.stdout.write(f"  Sexo: {row.get('SEXO', '')}")
        
        # Mostrar algunas materias como ejemplo
        self.stdout.write(f"  Materias (primeras 3):")
        contador = 0
        for codigo, nombre in materias_dict.items():
            if contador >= 3:
                break
            
            # Buscar P1 para esta materia
            col_p1 = f"{codigo}_P1"
            if col_p1 in row and not pd.isna(row[col_p1]):
                p1 = row[col_p1]
                self.stdout.write(f"    {codigo}: P1 = {p1}")
                contador += 1
    
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
    
    def procesar_carrera(self, df, carrera, materias_dict, limite):
        """Procesa una carrera completa (DC o ILI)"""
        self.stdout.write(f"\n=== PROCESANDO CARRERA {carrera} ===")
        
        df_limpio = self.limpiar_dataframe(df)
        
        if len(df_limpio) == 0:
            self.stdout.write(self.style.WARNING(f'No hay datos válidos para procesar en la carrera {carrera}'))
            return
        
        # Contadores
        alumnos_creados = 0
        alumnos_actualizados = 0
        materias_creadas = 0
        calificaciones_creadas = 0
        calificaciones_actualizadas = 0
        
        # Crear materias primero
        for codigo, nombre in materias_dict.items():
            materia, created = Materia.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': nombre}
            )
            if created:
                materias_creadas += 1
        
        # Determinar cuántas filas procesar
        total_filas = len(df_limpio)
        if limite > 0:
            total_filas = min(limite, total_filas)
        
        self.stdout.write(f'Procesando {total_filas} alumnos...')
        
        # Procesar cada alumno
        for index in range(total_filas):
            row = df_limpio.iloc[index]
            
            # Crear o actualizar alumno
            alumno, created = self.crear_o_actualizar_alumno(row, carrera)
            
            if alumno:
                if created:
                    alumnos_creados += 1
                else:
                    alumnos_actualizados += 1
                
                # Crear calificaciones para cada materia
                for codigo in materias_dict.keys():
                    try:
                        materia = Materia.objects.get(codigo=codigo)
                        calif_created = self.crear_calificacion(row, alumno, materia, codigo, carrera)
                        
                        if calif_created:
                            calificaciones_creadas += 1
                        else:
                            calificaciones_actualizadas += 1
                    except Materia.DoesNotExist:
                        continue
            
            # Mostrar progreso
            if (index + 1) % 5 == 0:
                self.stdout.write(f'  Procesados {index + 1} alumnos...')
        
        # Estadísticas
        self.stdout.write(self.style.SUCCESS(f'\nESTADÍSTICAS - CARRERA {carrera}:'))
        self.stdout.write(f'  Alumnos creados: {alumnos_creados}')
        self.stdout.write(f'  Alumnos actualizados: {alumnos_actualizados}')
        self.stdout.write(f'  Materias: {len(materias_dict)}')
        self.stdout.write(f'  Calificaciones procesadas: {calificaciones_creadas + calificaciones_actualizadas}')
    
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
    
    def crear_o_actualizar_alumno(self, row, carrera):
        """Crea o actualiza un alumno"""
        try:
            matricula_raw = row.get('MATRÍCULA')
            matricula = self.obtener_matricula(matricula_raw)
            
            if not matricula:
                return None, False
            
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
            
            # Semestre
            semestre = str(row.get('SEMESTRE', 'QUINTO')).strip()
            
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
                    'carrera': carrera,
                    'activo': True,
                }
            )
            
            if created:
                self.stdout.write(f'  ✓ Alumno creado: {matricula}')
            else:
                self.stdout.write(f'  ↻ Alumno actualizado: {matricula}')

            return alumno, created
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al crear alumno: {str(e)}'))
            return None, False
    
    def crear_calificacion(self, row, alumno, materia, codigo_materia, carrera):
        """Crea una calificación para un alumno en una materia"""
        try:
            # Encontrar las columnas en el Excel
            p1_col = f"{codigo_materia}_P1"
            p2_col = f"{codigo_materia}_P2"
            p3_col = f"{codigo_materia}_P3"
            ef_col = f"{codigo_materia}_EF"  # Examen Final
            
            # Para ILI, la última materia (C5262) usa PS y ES en lugar de PP y EF
            if carrera == 'ILI' and codigo_materia == 'C5262':
                pp_col = f"{codigo_materia}_PS"
                ef_col = f"{codigo_materia}_ES"
            else:
                pp_col = f"{codigo_materia}_PP"
            
            # Obtener valores
            p1 = self.convertir_a_decimal(row.get(p1_col)) if p1_col in row else None
            p2 = self.convertir_a_decimal(row.get(p2_col)) if p2_col in row else None
            p3 = self.convertir_a_decimal(row.get(p3_col)) if p3_col in row else None
            examen_final = self.convertir_a_decimal(row.get(ef_col)) if ef_col in row else None
            
            # Solo crear si hay al menos un dato
            tiene_datos = any(val is not None for val in [p1, p2, p3, examen_final])
            
            if not tiene_datos:
                return False
            
            # Crear o actualizar calificación
            calificacion, created = Calificacion.objects.update_or_create(
                alumno=alumno,
                materia=materia,
                defaults={
                    'p1': p1,
                    'p2': p2,
                    'p3': p3,
                    'examen_final': examen_final,
                }
            )
            
            # El método save() del modelo calculará automáticamente:
            # - promedio_parciales
            # - calificacion_final
            calificacion.save()
            
            # Mostrar para debug
            self.stdout.write(f"    {codigo_materia}: P1={p1}, P2={p2}, P3={p3}, EF={examen_final}, " +
                           f"PP={calificacion.promedio_parciales}, CF={calificacion.calificacion_final}")
            
            return created
        
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error en calificación {codigo_materia}: {str(e)}'))
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