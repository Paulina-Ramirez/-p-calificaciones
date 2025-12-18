# alumnos/management/commands/importar_excel.py - VERSIÓN FINAL CORREGIDA
import pandas as pd
import os
import re
from django.core.management.base import BaseCommand
from alumnos.models import Alumno, Materia, Calificacion
from django.utils import timezone
from decimal import Decimal
import numpy as np

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
                self.stdout.write(f"  Columnas: {len(primer_semestre_df.columns)}")
            
            if semestre_a_importar in ['TERCERO', 'AMBOS']:
                self.stdout.write("Cargando hoja TERCER SEMESTRE...")
                tercer_semestre_df = pd.read_excel(excel_path, sheet_name='TERCER SEMESTRE')
                semestres_df['TERCERO'] = tercer_semestre_df
                self.stdout.write(f"  Filas cargadas: {len(tercer_semestre_df)}")
                self.stdout.write(f"  Columnas: {len(tercer_semestre_df.columns)}")
            
            # Procesar cada semestre
            for semestre_nombre, df in semestres_df.items():
                # Para el tercer semestre, necesitamos limpiar los espacios en los nombres de columna
                df = self.preparar_dataframe(df, semestre_nombre)
                
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
    
    def preparar_dataframe(self, df, semestre_nombre):
        """Prepara el DataFrame para procesamiento"""
        # Primero hacer una copia
        df = df.copy()
        
        # Limpiar nombres de columna
        df.columns = [self.limpiar_nombre_columna(col, semestre_nombre) for col in df.columns]
        
        return df
    
    def limpiar_nombre_columna(self, col, semestre_nombre):
        """Limpia un nombre de columna específico"""
        if pd.isna(col):
            return ''
        
        col_str = str(col).strip()
        
        # Para columnas de calificaciones del tercer semestre, eliminar espacios internos
        if semestre_nombre == 'TERCERO' and re.match(r'^C\d{4}\s+[A-Z]', col_str):
            # Ejemplo: "C3023 P1" -> "C3023P1"
            col_str = col_str.replace(' ', '')
        
        # Reemplazar múltiples espacios por uno solo
        col_str = re.sub(r'\s+', ' ', col_str)
        
        return col_str
    
    def modo_prueba(self, df, semestre_nombre, limite):
        """Modo de prueba que solo analiza el archivo"""
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"MODO PRUEBA - SEMESTRE {semestre_nombre}")
        self.stdout.write(f"{'='*60}")
        
        # Mostrar información general
        self.stdout.write(f"Total filas: {len(df)}")
        self.stdout.write(f"Total columnas: {len(df.columns)}")
        
        # Identificar materias
        materias = self.identificar_materias(df)
        self.stdout.write(f"\nMaterias identificadas ({len(materias)}):")
        for materia in sorted(materias):
            self.stdout.write(f"  {materia}")
        
        # Analizar algunas filas de ejemplo
        filas_a_mostrar = min(limite if limite > 0 else 3, len(df))
        self.stdout.write(f"\nAnalizando {filas_a_mostrar} registros de ejemplo:")
        
        for i in range(filas_a_mostrar):
            row = df.iloc[i]
            matricula = self.obtener_valor(row, 'MATRÍCULA')
            
            if not matricula:
                continue
            
            matricula_str = self.formatear_matricula(matricula)
            
            self.stdout.write(f"\n--- Registro #{i+1} ---")
            self.stdout.write(f"Matrícula: {matricula_str}")
            self.stdout.write(f"Nombre: {self.obtener_valor(row, 'NOMBRE(S)')}")
            self.stdout.write(f"Semestre: {self.obtener_valor(row, 'SEMESTRE')}")
            self.stdout.write(f"Grupo: {self.obtener_valor(row, 'GRUPO')}")
            self.stdout.write(f"Sexo: {self.obtener_valor(row, 'SEXO')}")
            
            # Mostrar promedios generales
            self.stdout.write("\nPromedios generales:")
            promedios = [
                ('PROM. AL 1ER PARCIAL', 'PROM. AL 1ER PARCIAL'),
                ('PROM. AL 2° PARCIAL', 'PROM. AL 2° PARCIAL'),
                ('PROM. AL 3ER PARCIAL', 'PROM. AL 3ER PARCIAL'),
                ('PROM. FINAL', 'PROM. FINAL')
            ]
            
            for display_name, col_name in promedios:
                valor = self.obtener_valor(row, col_name)
                if valor is not None:
                    self.stdout.write(f"  {display_name}: {valor}")
            
            # Mostrar calificaciones de 2 materias de ejemplo
            if materias:
                self.stdout.write("\nCalificaciones de ejemplo (2 materias):")
                materias_ejemplo = sorted(materias)[:2]
                
                for materia in materias_ejemplo:
                    self.stdout.write(f"\n  Materia: {materia}")
                    
                    # Obtener todas las calificaciones para esta materia
                    tipos = ['P1', 'P2', 'P3', 'PP', 'EF', 'CF']
                    for tipo in tipos:
                        columna = f'{materia}{tipo}'
                        valor = self.obtener_valor(row, columna)
                        if valor is not None:
                            self.stdout.write(f"    {tipo}: {valor}")
    
    def identificar_materias(self, df):
        """Identifica los códigos de materia en el DataFrame"""
        materias = set()
        
        for columna in df.columns:
            if isinstance(columna, str) and columna.startswith('C'):
                # Extraer el código de materia (primeros 5 caracteres: C + 4 dígitos)
                match = re.match(r'^(C\d{4})', columna)
                if match:
                    codigo = match.group(1)
                    materias.add(codigo)
        
        return materias
    
    def obtener_valor(self, row, columna_buscada):
        """Busca un valor en la fila por nombre de columna"""
        # Primero buscar coincidencia exacta
        if columna_buscada in row.index:
            valor = row[columna_buscada]
            return None if pd.isna(valor) else valor
        
        # Si no encuentra, buscar coincidencia insensible a mayúsculas y espacios
        columna_buscada_norm = columna_buscada.upper().replace(' ', '').replace('(', '').replace(')', '')
        
        for col in row.index:
            if isinstance(col, str):
                col_norm = col.upper().replace(' ', '').replace('(', '').replace(')', '')
                if columna_buscada_norm == col_norm:
                    valor = row[col]
                    return None if pd.isna(valor) else valor
        
        return None
    
    def procesar_semestre(self, df, semestre_nombre, limite):
        """Procesa un DataFrame de un semestre específico"""
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f"PROCESANDO SEMESTRE: {semestre_nombre}")
        self.stdout.write(f"{'='*60}")
        
        # Contadores para estadísticas
        stats = {
            'alumnos_creados': 0,
            'alumnos_actualizados': 0,
            'materias_creadas': 0,
            'calificaciones_creadas': 0,
            'calificaciones_actualizadas': 0,
            'errores': 0
        }
        
        # Primero, crear todas las materias del semestre
        materias_dict = self.crear_materias_desde_dataframe(df, semestre_nombre)
        stats['materias_creadas'] = len(materias_dict)
        
        # Determinar cuántas filas procesar
        total_filas = len(df)
        if limite > 0 and limite < total_filas:
            total_filas = limite
        
        self.stdout.write(f'Procesando {total_filas} de {len(df)} filas...')
        self.stdout.write(f'Encontradas {len(materias_dict)} materias')
        
        # Iterar por cada fila (alumno)
        for index in range(total_filas):
            row = df.iloc[index]
            
            try:
                # Saltar filas vacías o sin matrícula
                matricula = self.obtener_valor(row, 'MATRÍCULA')
                if not matricula or str(matricula).strip() == '':
                    continue
                
                matricula_str = self.formatear_matricula(matricula)
                
                # Mostrar progreso
                if (index + 1) % 5 == 0:
                    self.stdout.write(f'  Progreso: {index + 1}/{total_filas} alumnos procesados')
                
                # Crear o actualizar alumno
                alumno, created = self.crear_o_actualizar_alumno(row, semestre_nombre, matricula_str)
                
                if not alumno:
                    stats['errores'] += 1
                    continue
                
                if created:
                    stats['alumnos_creados'] += 1
                else:
                    stats['alumnos_actualizados'] += 1
                
                # Para cada materia, crear calificación
                for codigo_materia, materia_obj in materias_dict.items():
                    calificacion, calif_created = self.crear_calificacion(
                        row, alumno, materia_obj, semestre_nombre, codigo_materia
                    )
                    
                    if calificacion:
                        if calif_created:
                            stats['calificaciones_creadas'] += 1
                        else:
                            stats['calificaciones_actualizadas'] += 1
            
            except Exception as e:
                stats['errores'] += 1
                self.stdout.write(self.style.ERROR(f'Error en fila {index+1}: {str(e)}'))
        
        # Mostrar estadísticas finales
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS(f"ESTADÍSTICAS - SEMESTRE {semestre_nombre}"))
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"  ✓ Alumnos creados: {stats['alumnos_creados']}")
        self.stdout.write(f"  ✓ Alumnos actualizados: {stats['alumnos_actualizados']}")
        self.stdout.write(f"  ✓ Materias: {stats['materias_creadas']}")
        self.stdout.write(f"  ✓ Calificaciones creadas: {stats['calificaciones_creadas']}")
        self.stdout.write(f"  ✓ Calificaciones actualizadas: {stats['calificaciones_actualizadas']}")
        if stats['errores'] > 0:
            self.stdout.write(self.style.WARNING(f"  ⚠ Errores: {stats['errores']}"))
        self.stdout.write(f"{'='*60}")
    
    def formatear_matricula(self, valor):
        """Formatea la matrícula correctamente"""
        if pd.isna(valor):
            return ''
        
        # Convertir a string y limpiar
        matricula_str = str(valor).strip()
        
        # Si tiene decimal .0, removerlo
        if matricula_str.endswith('.0'):
            matricula_str = matricula_str[:-2]
        
        return matricula_str
    
    def crear_materias_desde_dataframe(self, df, semestre_nombre):
        """Identifica y crea las materias a partir del DataFrame"""
        materias_dict = {}
        
        # Identificar todos los códigos únicos
        codigos_materias = self.identificar_materias(df)
        
        self.stdout.write(f'Identificando {len(codigos_materias)} materias...')
        
        # Diccionario de nombres de materias
        nombres_materias = {
            # Primer semestre
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
            # Tercer semestre
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
        
        for codigo in sorted(codigos_materias):
            try:
                # Obtener nombre de la materia
                nombre = nombres_materias.get(codigo, f'Materia {codigo}')
                
                # Crear o obtener la materia
                materia, created = Materia.objects.get_or_create(
                    codigo=codigo,
                    defaults={
                        'nombre': nombre,
                        'semestre': semestre_nombre
                    }
                )
                
                materias_dict[codigo] = materia
                
                if created:
                    self.stdout.write(f'  ✓ Materia creada: {codigo} - {nombre}')
                else:
                    self.stdout.write(f'  → Materia existente: {codigo}')
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ✗ Error con materia {codigo}: {str(e)}'))
        
        return materias_dict
    
    def crear_o_actualizar_alumno(self, row, semestre, matricula):
        """Crea o actualiza un alumno a partir de una fila del DataFrame"""
        try:
            # Parsear nombres
            nombre_completo = self.obtener_valor(row, 'NOMBRE(S)') or ''
            nombres = str(nombre_completo).split()
            
            primer_nombre = nombres[0] if len(nombres) > 0 else ''
            segundo_nombre = ' '.join(nombres[1:]) if len(nombres) > 1 else ''
            
            # Obtener otros datos
            grupo = self.obtener_valor(row, 'GRUPO') or ''
            sexo = self.obtener_valor(row, 'SEXO') or ''
            
            # Obtener promedios generales del alumno
            prom_primer_parcial = self.convertir_a_decimal(self.obtener_valor(row, 'PROM. AL 1ER PARCIAL'))
            prom_segundo_parcial = self.convertir_a_decimal(self.obtener_valor(row, 'PROM. AL 2° PARCIAL'))
            prom_tercer_parcial = self.convertir_a_decimal(self.obtener_valor(row, 'PROM. AL 3ER PARCIAL'))
            examen_final = self.convertir_a_decimal(self.obtener_valor(row, 'PROM. FINAL'))
            
            # Calcular promedio final si tenemos todos los datos
            prom_final_calculado = None
            if all(x is not None for x in [prom_primer_parcial, prom_segundo_parcial, prom_tercer_parcial, examen_final]):
                prom_parciales = (prom_primer_parcial + prom_segundo_parcial + prom_tercer_parcial) / 3
                prom_final_calculado = (prom_parciales + examen_final) / 2
                prom_final_calculado = round(prom_final_calculado, 1)
            
            # Crear o actualizar alumno
            alumno, created = Alumno.objects.update_or_create(
                matricula=matricula,
                defaults={
                    'primer_apellido': self.obtener_valor(row, 'PRIMER APELLIDO') or '',
                    'segundo_apellido': self.obtener_valor(row, 'SEGUNDO APELLIDO') or '',
                    'primer_nombre': primer_nombre,
                    'segundo_nombre': segundo_nombre,
                    'semestre': semestre,
                    'grupo': str(grupo).strip(),
                    'sexo': str(sexo).strip().upper(),
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
            self.stdout.write(self.style.ERROR(f'  ✗ Error al crear alumno {matricula}: {str(e)}'))
            return None, False
    
    def crear_calificacion(self, row, alumno, materia, semestre, codigo_materia):
        """Crea una calificación para un alumno en una materia específica"""
        try:
            # Buscar todas las calificaciones para esta materia
            valores = {
                'p1': self.obtener_calificacion_por_materia(row, codigo_materia, 'P1'),
                'p2': self.obtener_calificacion_por_materia(row, codigo_materia, 'P2'),
                'p3': self.obtener_calificacion_por_materia(row, codigo_materia, 'P3'),
                'pp': self.obtener_calificacion_por_materia(row, codigo_materia, 'PP'),
                'ef': self.obtener_calificacion_por_materia(row, codigo_materia, 'EF'),
                'cf': self.obtener_calificacion_por_materia(row, codigo_materia, 'CF'),
            }
            
            # Verificar si hay datos para esta materia
            tiene_datos = any(v is not None for v in valores.values())
            
            if not tiene_datos:
                return None, False
            
            # Crear o actualizar calificación
            calificacion, created = Calificacion.objects.update_or_create(
                alumno=alumno,
                materia=materia,
                semestre=semestre,
                defaults={
                    'p1': valores['p1'],
                    'p2': valores['p2'],
                    'p3': valores['p3'],
                    'promedio_semestral': valores['pp'],
                    'examen_final': valores['ef'],
                    'calificacion_final': valores['cf'],
                }
            )
            
            return calificacion, created
            
        except Exception as e:
            # Silenciar errores de materias sin datos
            return None, False
    
    def obtener_calificacion_por_materia(self, row, codigo_materia, tipo):
        """Obtiene una calificación específica para una materia"""
        # Construir el nombre de columna
        nombre_columna = f'{codigo_materia}{tipo}'
        
        valor = self.obtener_valor(row, nombre_columna)
        if valor is None:
            return None
        
        if tipo in ['P1', 'P2', 'P3']:
            return self.convertir_a_entero(valor)
        else:
            return self.convertir_a_decimal(valor)
    
    def convertir_a_entero(self, valor):
        """Convierte un valor a entero"""
        if pd.isna(valor):
            return None
        
        try:
            # Si es string, limpiar
            if isinstance(valor, str):
                valor = valor.strip()
                if valor == '':
                    return None
            
            # Convertir a float y luego a int
            valor_float = float(valor)
            return int(round(valor_float))
            
        except (ValueError, TypeError):
            return None
    
    def convertir_a_decimal(self, valor):
        """Convierte un valor a Decimal"""
        if pd.isna(valor):
            return None
        
        try:
            # Si es string, limpiar
            if isinstance(valor, str):
                valor = valor.strip()
                if valor == '':
                    return None
                # Reemplazar comas por puntos
                valor = valor.replace(',', '.')
            
            # Convertir a float y redondear a 1 decimal
            valor_float = float(valor)
            return round(valor_float, 1)
            
        except (ValueError, TypeError):
            return None